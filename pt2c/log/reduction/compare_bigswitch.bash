#!/bin/bash

cat average.log | awk 'BEGIN{count=0;}{count+=5; lr=$6; bs=count/$2; printf "%d %f %f %f\n", count, lr, bs, lr/bs}' >> data.log
