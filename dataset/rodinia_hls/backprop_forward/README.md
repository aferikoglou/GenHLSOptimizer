
backprop_forward @MPSoC ZCU102
==============================

* Target kernel freq. : 300 MHz

**Latency and resources utilization for a single FPGA kernel**
  

|Version|Latency|BRAM Util.|DSP Util.|FF Util.|LUT Util.|
| :---: | :---: | :---: | :---: | :---: | :---: |
|Unoptimized w/o Vitis 2020.2 opts|245.74 ms|31 %|0 %|0 %|7 %|
|Unoptimized with Vitis 2020.2 opts|222.78 ms|32 %|0 %|1 %|8 %|
|Optimized w/o Vitis 2020.2 opts|57.44 ms|39 %|10 %|18 %|35 %|
|Optimized with Vitis 2020.2 opts|57.31 ms|39 %|10 %|18 %|35 %|
