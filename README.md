# HLS Directive DSE based on Genetic Algorithms

In this project we created an optimizer able to automatically perform High-Level Synthesis directives Design Space Exploration leveraging genetic algorithms. 

**Supported HLS Directives**:
* Loop Pipiline
* Loop Unroll
* Array Partition

**Optimizer Inputs**:
1. synthesizable C/C++ source code annotated with labels in each action point i.e. array, loop (1st action point will be annotated with label L1, 2nd with label L2 etc.)
2. kernel_info.txt that provides a) the top level function name and b) information for each action point. For loop action points users have to provide the loop tripcount and for array action points users have to provide its name as well as the size of each array dimension.

**Optimizer Outputs**:
1. pareto optimal kernel source codes
2. info.csv that describes the pareto optimal kernel source code tradeoffs
3. database with the examined directives configurations and their corresponding latencies and resources (BRAM%, DSP%, LUT% and FF%)
4. a json file that provides statistics for the database

In the dataset and databases directory sample inputs and outputs can be found.

## Getting Started

These instructions will get you a copy of the project on your local machine.

### Prerequisites

This project was tested on Ubuntu 18.04.6 LTS (GNU/Linux 5.4.0-122-generic x86_64) with Python 3.6.9 and Vitis 2021.1 suite installed. 

In addition, the following libraries are needed:
* [pymoo](https://pypi.org/project/pymoo/) (v0.5.0)
* [sqlitedict](https://pypi.org/project/sqldict/) (v2.0.0)
* [psutil](https://pypi.org/project/psutil/) (v5.9.0)

which can be simply installed using the following command.

```bash
python3 -m pip install -r requirements.txt
```

### Run

After downloading the software in the *Prerequisites* section you can clone this repository on your local machine.

*Start the HLS directives Design Space Exploration*

```bash
./exec.sh run APP_NAME EXTENSION
```

*Example*

```bash
./exec.sh run rodinia-knn-1-tiling .cpp
```