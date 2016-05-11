#!/usr/bin/env python3
from pulp import *

def gml2topology(filename):
    import re

    f = open(filename)
    data = f.read()

    node_data = re.findall(r'node \[([^\]]*)\]', data, re.DOTALL)
    nodes = {}
    for n in node_data:
        info = [x.strip().split(' ', 1) for x in n.split('\n')]
        info = {x[0].lower(): x[1] for x in info if len(x) == 2}
        nodes[info['id']] = info

    edge_data = re.findall(r'edge \[([^\]]*)\]', data, re.DOTALL)
    edges = {}
    for e in edge_data:
        info = [x.strip().split(' ', 1) for x in e.split('\n')]
        info = {x[0].lower(): x[1] for x in info if len(x) == 2}
        info['id'] = '{}-{}'.format(info['source'], info['target'])
        edges[info['id']] = info

    graph = { 'nodes': nodes, 'links': edges }
    return graph

def is_internal(node):
    return ('internal' in node) and (node['internal'] == '1')

def is_internal_link(nodes, link):
    return is_internal(nodes[link['source']]) and is_internal(nodes[link['target']])

def setup_capacity(topo):
    nodes = topo['nodes']
    edges = topo['links']

    cap_i2i = { n['id']: [] for n in nodes.values() }
    cap_i2c = { n['id']: [] for n in nodes.values() }

    link_with_speed = [e for e in edges.values() if 'linkspeedraw' in e]
    link_without_speed = [e for e in edges.values() if not 'linkspeedraw' in e]
    i2i_link_with_speed = [e for e in link_with_speed if is_internal_link(nodes, e)]
    i2c_link_with_speed = [e for e in link_with_speed if not is_internal_link(nodes, e)]

    if len(link_with_speed) == 0:
        return False

    average_linkspeed = lambda links: sum([float(e['linkspeedraw']) for e in links])/len(links)
    total_average = average_linkspeed(link_with_speed)
    average_i2i = total_average if len(i2i_link_with_speed) == 0 else average_linkspeed(i2i_link_with_speed)
    average_i2c = total_average if len(i2c_link_with_speed) == 0 else average_linkspeed(i2c_link_with_speed)
    for e in link_with_speed:
        capacity = float(e['linkspeedraw'])
        if is_internal_link(nodes, e):
            cap_i2i[e['source']].append(capacity)
            cap_i2i[e['target']].append(capacity)
        else:
            cap_i2c[e['source']].append(capacity)
            cap_i2c[e['target']].append(capacity)

    cap_i2i = { x: average_i2i if len(y) == 0 else sum(y)/len(y) for x, y in cap_i2i.items() }
    cap_i2c = { x: average_i2c if len(y) == 0 else sum(y)/len(y) for x, y in cap_i2c.items() }

    for e in link_without_speed:
        if is_internal_link(nodes, e):
            e['linkspeedraw'] = str((cap_i2i[e['source']] + cap_i2i[e['target']])/2)
        else:
            e['linkspeedraw'] = str((cap_i2c[e['source']] + cap_i2c[e['target']])/2)

    return True

def evaluate_topology(topology):
    nodes = topology['nodes']
    internal = len([x for x in nodes.values() if is_internal(x)])
    print('Internal: {}/{}'.format(internal, len(nodes)))

    edges = topology['links']
    internalLinks = [x for x in edges.values() if is_internal_link(nodes, x)]
    hasLinkSpeed = len([x for x in edges.values() if 'linkspeedraw' in x])
    print('Has LinkSpeed: {}/{}'.format(hasLinkSpeed, len(edges)))
    print('Internal Links: {}/{}'.format(len(internalLinks), len(edges)))
    hasInternalLinkSpeed = len([x for x in internalLinks if 'linkspeedraw' in x])
    print('Internal Links with LinkSpeed: {}/{}'.format(hasInternalLinkSpeed, len(internalLinks)))

def calculate_paths(topology):
    """Calculate the all pair shortest paths in a network using the Floyd-Warshall algorithm
    """
    nodes = topology['nodes']
    edges = topology['links']

    dist = [[len(nodes) + 1 for x in range(len(nodes))] for y in range(len(nodes))]
    paths = [[[] for x in range(len(nodes))] for y in range(len(nodes))]

    for e in edges.values():
        s, d = int(e['source']), int(e['target'])
        dist[s][d] = dist[d][s] = 1
        paths[s][d] = [e['id']]
        paths[d][s] = [e['id']]

    for k in range(len(nodes)):
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    paths[i][j] = paths[i][k] + paths[k][j]
    return paths

def generate_random_pair(topology, n):
    import random

    nodes = topology['nodes']

    customer_nodes = [_n['id'] for _n in nodes.values() if not is_internal(_n)]
    pairs = [random.sample(customer_nodes, 2) for i in range(n)]

    if (len(pairs) != n):
        print(len(pairs))
        print(n)


    #for test fix pairs (0,5) (1,4)
    # pair1 = ['0','5']
    # pair2 = ['1','4']
    # pairs = [pair1, pair2]

    return pairs

def link_merge(paths, topology):
    links = topology['links']
    merged_links = {}
    for id, path in paths.items():
        constraint_link_map = {}
        for link in path:
            edge = links[link]
            bd = edge['linkspeedraw']
            constraint_link_map[bd] = edge
        merged_links[id] = constraint_link_map
    return merged_links


def mecs(paths, topology, minus, link_path_map, bandwidth_map):
    #add LP problem
    prob = LpProblem("rsa", LpMaximize)

    #add variables
    variables = {}
    for id, path in paths.items():
        #add variable
        variables[id] = LpVariable(id, 0, None)


    #add objective
    #find all path through minus
    obj = sum([variables[p] for p in link_path_map[minus]])
    prob += obj, "obj"


    #add constraints
    constraint_num = 0
    for linkid,_paths in link_path_map.items():
        if linkid == minus:
            continue
        c = sum([variables[p] for p in _paths])
        linkspeed = bandwidth_map[linkid]
        prob += c <= linkspeed, "c"+linkid
        constraint_num += 1



    prob.solve()

    minimal = set()
    y = value(prob.objective)
    if bandwidth_map[minus] < y:
        minimal.update([minus])
    return minimal


def abstract_engine(paths, topology):
    path_link_map = link_merge(paths, topology)
    minimal = set()
    #construct link_path_map
    link_path_map = {}

    for path, links in path_link_map.items():
        for _, link in links.items():
            link_id = link['id']
            if link_id in link_path_map:
                link_path_map[link_id].append(path)
            else:
                _paths = []
                _paths.append(path)
                link_path_map[link_id] = _paths

    #construct bandwitdth_map
    edges = topology['links']
    bandwidth_map = { e['id'] : int(float(e['linkspeedraw'])) for e in edges.values() if e['id'] in link_path_map.keys()}



    for link, _ in link_path_map.items():
        minimal.update(mecs(path_link_map, topology, link, link_path_map, bandwidth_map))

    return minimal




def build_constraint_matrix(topology, pairs, flow_num):
    import time
    import random
    orig_paths = calculate_paths(topology)
    paths = { i+"-"+j: set(orig_paths[int(i)][int(j)]) for i,j in pairs }
    used_links = set()
    for _, path in paths.items():
        used_links |= path
    edges = topology['links']
    used_edges = [e for e in edges.values() if e['id'] in used_links]

    is_on_path = lambda e, path: 1 if e['id'] in path else 0
    # matrix = [[e['id'] for _, p in paths.items() if is_on_path(e,p)] + [e['linkspeedraw']] for e in used_edges]

    f = open(str(flow_num) + '.log', 'a')
    start = time.time()
    minimal = abstract_engine(paths, topology)
    end = time.time()
    f.writelines("origin: "+ str(len(used_links)) + " compressed: " + str(len(minimal)) + " ratio: " + str(float(len(minimal))/float(len(used_links))) + " time: " + str(end-start)+"\n")
    f.close()
    # print('{} {}'.format(len(used_edges), len(paths)))
    # for i,j in pairs:
    #     print('{} {}'.format(i, j))
    # for i in range(len(matrix)):
    #     print('\t'.join([str(j) for j in matrix[i]]))


def path_vector_constructor():
    a=2

if __name__=='__main__':
    import argparse
    import sys
    import os.path


    parser = argparse.ArgumentParser(description='Get constraints for UTE')
    parser.add_argument('-f', '--format',
                        help="the format of the topology file (currently only GML)")
    parser.add_argument('topologyfile',
                        help="the input file containing topology information")
    parser.add_argument('-eo', '--evaluate-only', action='store_true',
                        help='Evaluate the topology only')
    parser.add_argument('-pc', '--preprocess-capacity', action='store_true',
                        help='Preprocess the missing capacity for links')
    parser.add_argument('-n', '--number-of-random-pairs', type=int,
                        help='Number of randomly generated OD pairs')

    args = parser.parse_args(sys.argv[1:])
    ext = os.path.splitext(args.topologyfile)[1]
    if ext == ".gml":
        topo = gml2topology(args.topologyfile)
    else:
        exit(0)
    if args.preprocess_capacity:
        setup_capacity(topo)
    if args.evaluate_only:
        print(args.topologyfile)
        evaluate_topology(topo)
    else:
        #flows
        for i in range(5, 105, 5):
            for j in range(0, 10):
                pairs = generate_random_pair(topo, i)
                build_constraint_matrix(topo, pairs, i)
