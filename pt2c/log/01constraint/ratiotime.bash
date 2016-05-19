#!/bin/bash

cat average.log | awk 'BEGIN{count=0; ratio=0; time=0;}{count+=1; ratio+=$6; time+=$8}END{printf "ratio:%f time:%f\n",ratio/count,time/count}'
