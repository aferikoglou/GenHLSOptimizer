
streamcluster @MPSoC ZCU102
===========================

* Target kernel freq. : 300 MHz

**Latency and resources utilization for a single FPGA kernel**
  

|Version|Latency|BRAM Util.|DSP Util.|FF Util.|LUT Util.|
| :---: | :---: | :---: | :---: | :---: | :---: |
|Unoptimized w/o Vitis 2020.2 opts|8.97 us|11 %|0 %|1 %|3 %|
|Unoptimized with Vitis 2020.2 opts|8.97 us|11 %|0 %|1 %|2 %|
|Optimized w/o Vitis 2020.2 opts|1.36 us|34 %|16 %|22 %|36 %|
|Optimized with Vitis 2020.2 opts|1.36 us|34 %|56 %|45 %|60 %|
