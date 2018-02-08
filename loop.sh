#!/bin/bash
for i in `seq 1 10`; do
    echo $i
    ./linkCheck.py 66.82.228.131 npsrt H2ghes01 no_modem
done
