#!/bin/bash
for((i=1; i<=20; i++)); do
echo -e  "$((i*5)) \c" >> ratio.log
for j in "mecs/average.log" "01constraint/average.log" "mecs_parallel/8core/average.log" ; do

head -n $i  $j | tail -n 1  | awk '{printf("%f ", $6)}' >> ratio.log

done
echo "" >> ratio.log
done


