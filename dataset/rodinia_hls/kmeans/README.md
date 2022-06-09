
kmeans @MPSoC ZCU102
====================

* Target kernel freq. : 300 MHz

**Latency and resources utilization for a single FPGA kernel**
  

|Version|Latency|BRAM Util.|DSP Util.|FF Util.|LUT Util.|
| :---: | :---: | :---: | :---: | :---: | :---: |
|Unoptimized w/o Vitis 2020.2 opts|3.14 us|41 %|0 %|0 %|14 %|
|Unoptimized with Vitis 2020.2 opts|1.96 us|41 %|0 %|0 %|10 %|
|Optimized w/o Vitis 2020.2 opts|1.57 us|49 %|47 %|36 %|56 %|
|Optimized with Vitis 2020.2 opts|1.52 us|49 %|47 %|36 %|56 %|
