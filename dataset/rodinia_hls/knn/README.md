
knn @MPSoC ZCU102
=================

* Target kernel freq. : 300 MHz

**Latency and resources utilization for a single FPGA kernel**
  

|Version|Latency|BRAM Util.|DSP Util.|FF Util.|LUT Util.|
| :---: | :---: | :---: | :---: | :---: | :---: |
|Unoptimized w/o Vitis 2020.2 opts|34.15 us|3 %|0 %|0 %|6 %|
|Unoptimized with Vitis 2020.2 opts|34.15 us|3 %|1 %|3 %|30 %|
|Optimized w/o Vitis 2020.2 opts|20.50 us|1 %|8 %|42 %|20 %|
|Optimized with Vitis 2020.2 opts|20.50 us|1 %|8 %|42 %|20 %|
