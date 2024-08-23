# HLS Directives Design Space Exploration Using Genetic Algorithms

This project features an optimizer designed to automatically conduct High-Level Synthesis (HLS) directives Design Space Exploration (DSE) through genetic algorithms.

**Supported HLS Directives:**
- Loop Pipeline
- Loop Unroll
- Array Partition

**Optimizer Inputs:**
1. Synthesizable C/C++ source code with labels at each action point (e.g., arrays, loops). Action points are labeled sequentially (L1, L2, etc.).
2. `kernel_info.txt` that includes:
   - **a)** The top-level function name
   - **b)** Details for each action point, including loop trip counts for loop action points and array names with dimension sizes for array action points.

**Optimizer Outputs:**
1. Pareto-optimal kernel source codes
2. `info.csv` detailing trade-offs among Pareto-optimal kernel source codes
3. A database containing examined directive configurations with their respective latencies and resource usage (BRAM%, DSP%, LUT%, and FF%)
4. `APP_NAME.json` providing statistics for the database

Sample inputs and outputs can be found in the `dataset` and `databases` directories.

## Getting Started

Follow these instructions to get a copy of the project on your local machine.

### Prerequisites

This project has been tested on Ubuntu 18.04.6 LTS with Python 3.6.9 and Vitis 2021.1 suite. Additionally, the following libraries are required:
- [pymoo](https://pypi.org/project/pymoo/) (v0.5.0)
- [sqlitedict](https://pypi.org/project/sqldict/) (v2.0.0)
- [psutil](https://pypi.org/project/psutil/) (v5.9.0)

Install these dependencies using:

```bash
python3 -m pip install -r requirements.txt
```

### Running the Project

After installing the necessary software from the *Prerequisites* section, clone this repository to your local machine.

**Execute the HLS Directives Design Space Exploration:**

```bash
./exec.sh run APP_NAME EXTENSION
```

**Example:**

```bash
./exec.sh run rodinia-knn-1-tiling .cpp
```