
reset
set terminal postscript landscape "Times-Roman" 24

set size 1.0, 0.8

set xlabel "Number of flows" font ",28"
set ylabel "Execution Time (ms)" font ",28"

set yrange [0:1200]
set key left top opaque horizontal

set style line 1 lt 1 lw 6 pt 1 ps 2
set style line 2 lt 1 lw 6 pt 2 ps 2
set style line 3 lt 1 lw 6 pt 3 ps 2
set style line 4 lt 1 lw 6 pt 4 ps 2


set output "parallel-time.eps"

set grid ytics

data="time.log"

plot    data using 1:2 w linesp ls 1 title " 1 core", \
	    data using 1:3 w linesp ls 2 title " 2 cores", \
	    data using 1:4 w linesp ls 3 title " 4 cores", \
	    data using 1:5 w linesp ls 4 title "8 cores", \
