#!/bin/bash
for((i=1; i<=4; i++)); do
echo -e  "$((i*5)) \c" >> time.log
for j in "mecs/average.log" "01constraint/average.log" "mecs_parallel/average.log" ; do

head -n $i  $j | tail -n 1  | awk '{printf("%f ", $8*1000)}' >> time.log

done
echo "" >> time.log
done


