#!/bin/sh

num_loops=5
sleep_time=2

for i in `seq $num_loops`
do
    printf 'Iteration %s\n' $i
    printf '============\n'
    python linkCheck.py 66.82.228.131 npsrt H2ghes01;
    if [ "$i" -lt "$num_loops" ]; then
        sleep $sleep_time
    fi
done
