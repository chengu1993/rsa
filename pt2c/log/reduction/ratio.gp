
reset
set terminal postscript landscape "Times-Roman" 24

set size 1.0, 0.8

set xlabel "Number of flows" font ",28"
set ylabel "Compression Ratio" font ",28"

set yrange [0:4]
set key left top

set style line 1 lt 1 lw 6 pt 1 ps 2
set style line 2 lt 1 lw 6 pt 2 ps 2


set output "link-reduction.eps"


data="link-reduction.log"

plot    data using 1:2 w linesp ls 1 title " Link Reduction", \
	    data using 1:3 w linesp ls 2 title " Big Switch", \
