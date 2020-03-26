# Evolutionary algorithm for plan optimizations.

I tested this code on Ubuntu 18.04.

To run the optimizer you need python packages deap, pandas and numpy.


## Remark
I will probably move the project to gitlab for better support of wiki


## How to start

run

    python3 main.py

The script will generate new generation every couple of seconds and immediately display a statistic for it. If this does not happen, check the section *Troubleshooting*.

After generation 1041, you will get an optimal solution. The script will write it to a file plan.csv and store statistics into statistics.csv.

## Troubleshooting

* Problem: On with Windows 10, the script does not display anything after the initial solution is generated.

    Reason: Multiprocessing does not work.

    Solution: Comment out the block

        pool = multiprocessing.Pool()
        toolbox.register("map", pool.map)

    in main.py.

## Notes
[General notes and ideas in German](doc/notes.md)


