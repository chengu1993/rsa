
reset
set terminal postscript landscape "Times-Roman" 24

set size 1.0, 0.8

set xlabel "Number of Instances" font ",28"
set ylabel "Execution Time (ms)" font ",28"

set yrange [1.0/64:10]
set key left top opaque horizontal

set style line 1 lt 1 lw 6 pt 1 ps 2
set style line 2 lt 1 lw 6 pt 2 ps 2
set style line 3 lt 1 lw 6 pt 3 ps 2
set style line 4 lt 1 lw 6 pt 4 ps 2
set style line 5 lt 1 lw 6 pt 5 ps 2
set style line 6 lt 1 lw 6 pt 6 ps 2

outputfile=sprintf("cpt-%s.eps", target)
set output outputfile

set logscale y 2
set ytics ("1/128" 1.0/128, "1/64" 1.0/64, "1/32" 1.0/32, "1/16" 1.0/16, "1/8" 1.0/8, "1/4" 1.0/4, "1/2" 1.0/2, "1" 1, "2" 2, "4" 4, "8" 8)
set grid ytics

data=sprintf("./results/core-%s-normalized-cpt", target)

plot    data using 1:2 w linesp ls 1 title " 2 threads", \
	    data using 1:3 w linesp ls 2 title " 4 threads", \
	    data using 1:4 w linesp ls 3 title " 8 threads", \
	    data using 1:5 w linesp ls 4 title "16 threads", \
	    data using 1:6 w linesp ls 5 title "32 threads", \
	    data using 1:7 w linesp ls 6 title "64 threads"
