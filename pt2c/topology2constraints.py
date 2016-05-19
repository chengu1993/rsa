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


    #for test fix pairs (0,5) (1,4)
    # pair1 = ['0','5']
    # pair2 = ['1','4']
    # pairs = [pair1, pair2]

    return pairs
#
# def link_merge(paths, topology):
#     links = topology['links']
#     merged_links = {}
#     for id, path in paths.items():
#         constraint_link_map = {}
#         for link in path:
#             edge = links[link]
#             bd = edge['linkspeedraw']
#             constraint_link_map[bd] = edge
#         merged_links[id] = constraint_link_map
#     return merged_links


def preprocessing_for_reduction(paths, topology):
    path_link_map = {}
    for id, path in paths.items():
        links = []
        for link_id in path:
            links.append(link_id)
        path_link_map[id] = links

    # construct link_path_map
    link_path_map = {}
    for path, links in path_link_map.items():
        for link_id in links:
            if link_id in link_path_map:
                link_path_map[link_id].append(path)
            else:
                _paths = []
                _paths.append(path)
                link_path_map[link_id] = _paths

    # construct bandwitdth_map
    edges = topology['links']
    bandwidth_map = {e['id']: int(float(e['linkspeedraw'])) for e in edges.values() if
                     e['id'] in link_path_map.keys()}

    return [path_link_map, link_path_map, bandwidth_map]

def preprocessing(paths, topology):
    path_link_map = {}
    for id, path in paths.items():
        links = []
        for link_id in path:
            links.append(link_id)
        path_link_map[id] = links

    # construct link_path_map
    link_path_map = {}
    for path, links in path_link_map.items():
        for link_id in links:
            if link_id in link_path_map:
                link_path_map[link_id].append(path)
            else:
                _paths = []
                _paths.append(path)
                link_path_map[link_id] = _paths

    # construct bandwitdth_map
    edges = topology['links']
    bandwidth_map = {e['id']: int(float(e['linkspeedraw'])) for e in edges.values() if
                     e['id'] in link_path_map.keys()}

    redundant = set()
    keys = [k for k in link_path_map.keys()]
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            link_id_1 = keys[i]
            link_id_2 = keys[j]
            if link_path_map[link_id_1] == link_path_map[link_id_2] and bandwidth_map[link_id_1] == bandwidth_map[
                link_id_2]:
                redundant.add(link_id_2)

    # delete redundant links in path_link_map
    for path_id, links in path_link_map.items():
        links = [x for x in links if x not in redundant]
        path_link_map[path_id] = links

    # path_link_map = { p:[x for x in links if x not in redundant] for p, links in path_link_map.items()}

    # delete redundant links in link_path_map
    for link_id in redundant:
        del link_path_map[link_id]

    # delete redundant links in bandwidth_map
    for link_id in redundant:
        del bandwidth_map[link_id]

    return [path_link_map, link_path_map, bandwidth_map]

def solve_lp(path_link_map, constraints, minus, link_path_map, bandwidth_map):
    #add LP problem
    prob = LpProblem("rsa", LpMaximize)

    #add variables
    variables = {}
    for path_id, path in path_link_map.items():
        #add variable
        variables[path_id] = LpVariable(path_id, 0, sys.maxsize)


    #add objective
    #find all path through minus
    obj = sum([variables[p] for p in link_path_map[minus]])
    prob += obj, "obj"


    #add constraints
    for link_id in constraints:
        if link_id == minus:
            continue
        _paths = link_path_map[link_id]
        c = sum([variables[p] for p in _paths])
        linkspeed = bandwidth_map[link_id]
        prob += c <= linkspeed, "c" + link_id

    prob.solve()
    return value(prob.objective)


def mecs(link_path_map, path_link_map, bandwidth_map):
    minimal = set()
    constraints = set()
    for link_id, _ in link_path_map.items():
        constraints.add(link_id)
    for link_id, _ in link_path_map.items():
        constraints.remove(link_id)
        y = solve_lp(path_link_map, constraints, link_id, link_path_map, bandwidth_map)
        if bandwidth_map[link_id] < y:
            minimal.add(link_id)
        constraints.add(link_id)
    return minimal


def find_minimal_element(constraints, bandwidth_map, link_path_map):

    minimal = sys.maxsize
    most_non_zero_coef = -1
    minimal_constraint = None;
    for constraint in constraints:
        if bandwidth_map[constraint] < minimal:
            minimal = bandwidth_map[constraint]
            minimal_constraint = constraint
            most_non_zero_coef = len(link_path_map[constraint])
        elif bandwidth_map[constraint] == minimal:
            if len(link_path_map[constraint]) > most_non_zero_coef:
                minimal_constraint = constraint
                most_non_zero_coef = len(link_path_map[constraint])
    return minimal_constraint



def _01constraints(link_path_map, path_link_map, bandwidth_map):
    minimal = set()
    constraints = set()
    for link_id, _ in link_path_map.items():
        constraints.add(link_id)
    while len(constraints) > 0:
        constraint = find_minimal_element(constraints, bandwidth_map, link_path_map)
        if  len(minimal) == 0:
            minimal.add(constraint)
        else:
            y = solve_lp(path_link_map, minimal, constraint, link_path_map, bandwidth_map)
            if bandwidth_map[constraint] < y:
                minimal.add(constraint)
        constraints.remove(constraint)
    return minimal

def abstract_engine(path_link_map, link_path_map, bandwidth_map):

    #return mecs(link_path_map, path_link_map, bandwidth_map)
    #return _01constraints(link_path_map, path_link_map, bandwidth_map)
    return mecs_paralell(link_path_map, path_link_map, bandwidth_map)


def mecs_paralell(link_path_map, path_link_map, bandwidth_map):
    from multiprocessing import Pool
    #create pool
    PROCESS = 4
    pool = Pool(PROCESS)

    minimal = set()
    constraints = set()
    results = {}
    for link_id, _ in link_path_map.items():
        constraints.add(link_id)
    for link_id, _ in link_path_map.items():
        results[link_id] = pool.apply_async(solve_lp, [path_link_map, constraints, link_id, link_path_map, bandwidth_map])

    pool.close()
    for link_id, y in results.items():
        if bandwidth_map[link_id] < y.get():
            minimal.add(link_id)
    return minimal


def build_constraint_matrix(topology, pairs, flow_num):
    import time


    start = time.time()
    orig_paths = calculate_paths(topology)
    end = time.time()
    path_calculate_time = end - start
    paths = {i+"-"+j: set(orig_paths[int(i)][int(j)]) for i, j in pairs}
    used_links = set()
    for _, path in paths.items():
        used_links |= path

    #preprocessing
    start = time.time()
    results = preprocessing(paths, topology)
    end = time.time()
    preprocessing_time = end - start
    path_link_map = results[0]
    link_path_map = results[1]
    bandwidth_map = results[2]



    #Aggregation Only
    # f = open(str(flow_num) + '.log', 'a')
    # start = time.time()
    # results = preprocessing(paths, topology)
    # link_path_map = results[1]
    # end = time.time()
    # f.writelines("origin: "+ str(len(used_links)) + " compressed: " + str(len(link_path_map)) + " ratio: " + str(float(len(link_path_map))/float(len(used_links))) + " time: " + str(end-start)+"\n")
    # f.close()



    # minimal = abstract_engine(path_link_map, link_path_map, bandwidth_map)

    # test write to file
    # f = open(str(flow_num) + '.log', 'a')
    start = time.time()
    minimal = abstract_engine(path_link_map, link_path_map, bandwidth_map)
    end = time.time()
    abstract_time = end -start
    # f.writelines("origin: "+ str(len(used_links)) + " compressed: " + str(len(minimal)) + " ratio: " + str(float(len(minimal))/float(len(used_links))) + " time: " + str(abstract_time)+"\n")
    # f.close()
    #
    # #
    results = preprocessing_for_reduction(paths, topology)
    path_link_map = results[0]
    link_path_map = results[1]
    #
    #

    #
    # minimal = set()
    # minimal.add("link0")
    # redundant = ["link1", "link2", "link3", "link4"]
    # link_path_map = {}
    # link_path_map["link0"] = ["path0", "path1", "path2", "path3"]
    # link_path_map["link1"] = ["path0", "path1"]
    # link_path_map["link2"] = ["path1", "path2"]
    # link_path_map["link3"] = ["path1", "path2", "path3"]
    # link_path_map["link4"] = ["path0", "path1", "path3"]
    #
    # path_link_map = {}
    # path_link_map["path0"] = ["link0", "link1", "link4"]
    # path_link_map["path1"] = ["link0", "link1", "link2", "link3", "link4"]
    # path_link_map["path2"] = ["link0", "link2", "link3"]
    # path_link_map["path3"] = ["link0", "link3", "link4"]


    # link reduction
    redundant = [x for x in used_links if x not in minimal]
    # origin = len(redundant)
    # #test write to file
    # f = open(str(flow_num) + '.log', 'a')
    start = time.time()
    link_reduction(redundant, minimal, link_path_map, path_link_map)
    end = time.time()
    reduction_time = end - start
    # compressed = len(redundant)
    # f.writelines("origin: "+ str(origin) + " compressed: " + str(compressed) + " ratio: " + str(float(compressed)/float(origin)) + " time: " + str(end-start)+"\n")
    # f.close()



    #overrall evaluation
    f = open(str(flow_num) + '.log', 'a')
    f.writelines("PathCompute: " + str(path_calculate_time) + " preprocessing: " + str(preprocessing_time) + " abstract: " + str(abstract_time) + " redunction: " + str(reduction_time) +"\n")
    f.close()


def link_aggregation():
    a=2

def reduce(minus, constraints, path_link_map, link_path_map):
    #add problem
    prob = LpProblem("reduce", LpMinimize)
    #add varaibles
    coef = {}
    remainder = {}
    for constraint in constraints:
        if constraint != minus:
            coef[constraint] = LpVariable(constraint, 0, 1, LpBinary)
    for path_id in path_link_map.keys():
        remainder[path_id] = LpVariable(path_id, 0, 1, LpBinary)
    #add obj
    obj = sum(x for x in remainder.values())
    prob += obj, "obj"

    #add contraints
    #one path maps to one contraint
    for path_id, links in path_link_map.items():
        minimal_links = [x for x in links if x in constraints if x != minus]
        c =  sum(coef[x] for x in minimal_links) + remainder[path_id]
        if path_id in link_path_map[minus]:
            c_obj = 1
        else:
            c_obj = 0
        prob += c == c_obj, "c"+path_id


    prob.solve()
    return remainder

def sort(redundant, link_path_map):
    for i in range(len(redundant)):
        for j in range(i+1, len(redundant)):
            coef1 = len(link_path_map[redundant[i]])
            coef2 = len(link_path_map[redundant[j]])
            if coef1 < coef2:
                redundant[i], redundant[j] = redundant[j], redundant[i]


def delete_link_from_redundant(link, redundant, link_path_map, path_link_map):
    redundant.remove(link)

    del link_path_map[link]

    for path_id, links in path_link_map.items():
        if link in links:
            links.remove(link)

def count_non_zeors(varaibles):
    count = 0
    for _, varaible in varaibles.items():
        count += value(varaible)
    return count


def link_reduction(redundant, minimal, link_path_map, path_link_map):
    add_link_count = 0
    #reduce redundant using minimal
    for link_id in redundant:
        result = reduce(link_id, minimal, path_link_map, link_path_map)
        if count_non_zeors(result) == 0:
            #can be represented by minial, and hence can be deleted
            delete_link_from_redundant(link_id, redundant, link_path_map, path_link_map)

    continue_flag = True
    while continue_flag:
        continue_flag = False
        sort(redundant, link_path_map)
        for link_id in redundant:

            result = reduce(link_id, redundant, path_link_map, link_path_map)
            link_count = len(link_path_map[link_id])
            result_count = 0
            for _, varaible in result.items():
                result_count += value(varaible)
            #delete origin link
            if result_count == 0:
                delete_link_from_redundant(link_id, redundant, link_path_map, path_link_map)
                continue_flag = True
                break;
            if count_non_zeors(result) > 0:

                if result_count < link_count: # has been reduced to smaller
                    delete_link_from_redundant(link_id, redundant, link_path_map, path_link_map)
                    continue_flag = True
                    #add new link result
                    #update redundant
                    _link_id = "add_link_" + str(add_link_count)
                    add_link_count += 1
                    redundant.append(_link_id)
                    #update link_path_map
                    _path = []
                    for path_id, varaible in result.items():
                        if value(varaible) == 1:
                            _path.append(path_id)
                    link_path_map[_link_id] = _path

                    #update path_link_map
                    for path_id, varaible in result.items():
                        if value(varaible) == 1:
                            path_link_map[path_id].append(_link_id)
                    break;
    return redundant





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
        for i in range(5, 105, 5):
            for j in range(0, 10):
                pairs = generate_random_pair(topo, i)
                build_constraint_matrix(topo, pairs, i)
        # for j in range(0, 10):
        #     pairs = generate_random_pair(topo, )
        #     build_constraint_matrix(topo, pairs, i)
