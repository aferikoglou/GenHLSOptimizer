
backprop @MPSoC ZCU102
======================

* Target kernel freq. : 300 MHz

**Latency and resources utilization for a single FPGA kernel**
  

|Version|Latency|BRAM Util.|DSP Util.|FF Util.|LUT Util.|
| :---: | :---: | :---: | :---: | :---: | :---: |
|Unoptimized w/o Vitis 2020.2 opts|3.33 ms|39 %|0 %|1 %|15 %|
|Unoptimized with Vitis 2020.2 opts|1.41 ms|43 %|6 %|6 %|22 %|
|Optimized w/o Vitis 2020.2 opts|1.61 ms|50 %|11 %|10 %|37 %|
|Optimized with Vitis 2020.2 opts|1.30 ms|50 %|11 %|10 %|37 %|
