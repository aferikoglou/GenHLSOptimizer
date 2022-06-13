#!/bin/bash

echo "Killing Vitis processes for "$USER
for pid in `ps -aux | grep $USER | grep vitis | awk '{print $2}'`;
do
       	echo $pid	
	kill $pid
done

