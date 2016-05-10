#!/bin/bash

touch evaluation.txt
for x in input/*.gml; do
	result=$(python topology2constraints.py -eo -pc -f GML $x)
	echo $result
	echo $result >> evaluation.txt
done
