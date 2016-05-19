#!/bin/bash

for logfile in `ls . | grep "\.log"`; do
cat $logfile | awk 'BEGIN{count=0; origin=0; compressed=0; ratio=0; time=0}{count=count+1; origin=origin+$2; compressed+=$4; ratio+=$6; time+=$8}END{printf "origin: %f compressed: %f ratio: %f mecstime: %f\n", origin/count,compressed/count,ratio/count,time/count}' >> average.log
done
