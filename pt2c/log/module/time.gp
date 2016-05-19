
reset
set terminal postscript landscape "Times-Roman" 24
set style data histogram
set style histogram
set style fill solid 0.4 border
set size 1.0, 0.8

set xlabel "Modules" font ",28"
set ylabel "Execution Time (ms)" font ",28"

set yrange [0:2]
set key top



set output "module.eps"


data="module.log"

plot    data using 2:xticlabels(1) title columnheader(2)
