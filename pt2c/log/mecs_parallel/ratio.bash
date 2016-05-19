#!/bin/bash
for((i=1; i<=20; i++)); do
echo -e  "$((i*5)) \c" >> ratio.log
for j in 1 2 4 8; do

head -n $i  $j"core/average.log"| tail -n 1  | awk '{printf("%f ", $6)}' >> ratio.log

done
echo "" >> ratio.log
done


