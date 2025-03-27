#!/usr/bin/python3

import read_data_new

project = "/home/schen/thesis/ibrowser2/s_demo/index"

bigWig1 = read_data_new.BigWig(project)
result1 = bigWig1.get(10,'1',['108','88','139'])

print(result1)