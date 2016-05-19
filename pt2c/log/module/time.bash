#!/bin/bash

cat average.log | awk 'BEGIN{count=0; path=0; pre=0; abstract=0; re=0;}{count+=1; path+=$2; pre+=$4; abstract+=$6; re+=$8}END{printf "path:%f pre:%f abstract:%f re:%f\n",path/count,pre/count,abstract/count,re/count}'
