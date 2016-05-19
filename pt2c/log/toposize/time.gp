
reset
set terminal postscript landscape "Times-Roman" 24

set size 1.0, 0.8

set xlabel "Topology size (#node)" font ",28"
set ylabel "Execution Time (ms)" font ",28"

set yrange [0:200]
set key left top

set style line 1 lt 1 lw 6 pt 1 ps 2
set style line 2 lt 1 lw 6 pt 2 ps 2
set style line 3 lt 1 lw 6 pt 3 ps 2


set output "topo_time.eps"

set grid xtics
set grid ytics
data="time.log"

plot    data using 1:2 w linesp ls 1 title " mecs", \
	    data using 1:3 w linesp ls 2 title " 01-constraint", \
	    data using 1:4 w linesp ls 3 title " mecs + parallel (8core)", \
