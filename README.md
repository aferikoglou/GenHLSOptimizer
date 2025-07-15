# HLS-driven Design Space Exploration Using Genetic Algorithms

**GenHLSOptimizer** is an automated optimizer for conducting **Design Space Exploration (DSE)** of **High-Level Synthesis (HLS)** directive configurations using **Genetic Algorithms**, specifically the **NSGA-II** algorithm. It enables fine-grained exploration and tuning of hardware performance vs. resource usage for HLS designs targeting **Xilinx/AMD FPGAs** via the **Vitis HLS** toolchain.

---

## Key Features

* **Supported Directives**:

  * `Loop Pipeline`
  * `Loop Unroll`
  * `Array Partition`

* **Multi-objective optimization** across:

  * Design Latency (msec)
  * BRAM%, DSP%, LUT%, and FF% Utilization

* **Parallelized evaluations**

---

## Inputs

1. **C/C++ source code** annotated with labeled action points (i.e. loops and arrays) such as `L1`, `L2`, etc.
2. **`kernel_info.txt`** file, generated using the companion tool [HLSAnalysisTools](https://github.com/aferikoglou/HLSAnalysisTools), which contains:

   * The top-level function name
   * Metadata for each action point such as the loop trip counts and array dimensions

---

## Output

* **SQLite Database** that logs every explored directive configuration along with its corresponding HLS performance and resource metrics. All databases are stored in the `databases/` directory, and users can directly extract Pareto-optimal configurations from them for further analysis or reuse.

---

## Getting Started

Follow these instructions to get a copy of the project on your local machine.

### Prerequisites

This project has been validated on **Ubuntu 18.04.6 LTS** with **Python 3.6.9** and the **Vitis 2021.1** toolchain. To ensure proper functionality, the following Python libraries are required:

* [`pymoo`](https://pypi.org/project/pymoo/) (version 0.5.0)
* [`sqlitedict`](https://pypi.org/project/sqldict/) (version 2.0.0)
* [`psutil`](https://pypi.org/project/psutil/) (version 5.9.0)

You can install all required dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

### Run

After downloading the software in the *Prerequisites* section you can clone this repository on your local machine.

**Perform HLS-based DSE for Xilinx/AMD FPGAs, targeting UltraScale+ MPSoC ZCU104 and Alveo U200 at 100, 200, and 300 MHz**

```bash
exec.sh run <ApplicationName> <Extension>
```

**Example: Generate the Databases for RodiniaHLS KNN Baseline Application**

```bash
exec.sh run RodiniaHLS-KNN-Baseline .cpp

Output

...

Top level function = workload
Input source code path = ./knn.cpp

DESIGN SPACE EXPLORATION FOR RodiniaHLS-KNN-Baseline FOR DEVICE WITH ID xczu7ev-ffvc1156-2-e AND TARGET CLOCK PERIOD 10 USEC

=====================================================================================
n_gen |  n_eval |   cv (min)   |   cv (avg)   |  n_nds  |     eps      |  indicator  
=====================================================================================
    1 |      18 |  0.00000E+00 |  0.00000E+00 |       6 |            - |            -
    2 |      24 |  0.00000E+00 |  0.00000E+00 |       6 |  0.00000E+00 |            f
    3 |      24 |  0.00000E+00 |  0.00000E+00 |       6 |  0.00000E+00 |            f
...

Database Analytics

Database Path = ./Databases/RodiniaHLS-KNN-Baseline_xczu7ev-ffvc1156-2-e_10.sqlite

Number of synthesis = 24

Synthesis timeout percentage = 0.000000 (0)
Synthesis failed percentage  = 0.000000 (0)
Synthesis success total percentage = 100.000000 (24)
- Synthesis feasible percentage = 100.000000 (24)
- Synthesis non feasible percentage = 0.000000 (0)

...

Top level function = workload
Input source code path = ./knn.cpp

DESIGN SPACE EXPLORATION FOR RodiniaHLS-KNN-Baseline FOR DEVICE WITH ID xcu200-fsgd2104-2-e AND TARGET CLOCK PERIOD 3.33 USEC

=====================================================================================
n_gen |  n_eval |   cv (min)   |   cv (avg)   |  n_nds  |     eps      |  indicator  
=====================================================================================
    1 |      18 |  0.00000E+00 |  0.00000E+00 |       6 |            - |            -
    2 |      24 |  0.00000E+00 |  0.00000E+00 |       6 |  0.00000E+00 |            f
    3 |      24 |  0.00000E+00 |  0.00000E+00 |       6 |  0.00000E+00 |            f
...

Database Analytics

Database Path = ./Databases/RodiniaHLS-KNN-Baseline_xcu200-fsgd2104-2-e_3.33.sqlite

Number of synthesis = 24

Synthesis timeout percentage = 0.000000 (0)
Synthesis failed percentage  = 0.000000 (0)
Synthesis success total percentage = 100.000000 (24)
- Synthesis feasible percentage = 100.000000 (24)
- Synthesis non feasible percentage = 0.000000 (0)

...

```
## Publication

If you find our project useful, please consider citing our paper:

```

```
