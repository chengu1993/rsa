#!/bin/bash

input=$1
if [ $2 ]; then
	output=$2
else
	output=$(echo $input | sed 's/gml/jpg/g' | sed 's/input/output/g')
fi
echo $output

cp $input __tmp
cat __tmp | sed 's/Source/_Source/g' | sed 's/id "e/_id "e/g' > ___tmp

gml2gv ___tmp | sed 's/Internal=1/color=blue,shape=box/g' \
		| sed 's/Internal=0/color=green/g' \
		| sed 's/LinkSpeed=/color=red,LinkSpeed=/g' \
		| dot -Tjpg -o $output

rm __tmp ___tmp
