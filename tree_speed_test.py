#!/usr/bin/python3

import time
import random
import numpy

import read_data as rd

from timer import tree_records, test_timer, records
from sys import argv

error = "Invaild input, see usage below"
usage = "Usage: tree_speed_test.py data_file test_file"

def main(args):
	data_file, test_file = args

	tests = []
	with open(test_file, "r") as tf:
		tf.readline()
		for line in tf:
			line = line.strip()
			if not line: continue
			items = line.split('\t')
			test = {'nSamples': int(items[0]), 'Length': int(items[1]), 'Times': int(items[2])}
			print(test)
			tests.append(test)

	test_folder = test_file.rpartition('/')[0]
	test_file_name = test_file.rpartition('/')[2]
	res_file = test_folder + '/' + test_file_name + '.result'

	data = rd.BigWig(data_file)
	chrom_sizes = data.chroms

	output = "Test for Drawing trees for Database: {}\n".format(data_file)

	for test in tests:
		for i in range(test['Times']):

			options = []
			if "--best-chrom" in options:
				chroms = list(chrom_sizes.items()) # [('chr1', 3000), ('chr2', 7200), ...]
				available_chrom = [x for x in chroms if x[1] >= test['Length']]
				if not available_chrom: 
					chrom = max(chroms, key = lambda x: x[1])[0]
				else:
					chrom = random.choice([x[0] for x in available_chrom])
			else:
				chrom = random.choice(list(chrom_sizes.keys()))

			samples = random.sample(data.available_samples, test['nSamples'])
			len_chrom = chrom_sizes[chrom]

			if test['Length'] > len_chrom:
				test['Length'] = len_chrom
				print("WARNING: Sequence length for testing has been cut to {}".format(test['Length']))

			start = random.randrange(1, len_chrom - test['Length'] + 2)
			end = start + test['Length'] - 1

			temp = data.get_tree(chrom, start, end, samples, return_format = "newick")

		condition = "nSamples\t{}\nLength\t{}\nTimes\t{}\n".format(test['nSamples'], test['Length'], test['Times'])
		output += condition
		output += "timer\tAverage\tStd\n"
		
		print("\nResults for Test Condition: \n{}\n".format(test))

		timer_list = ['sys', 'user', 'process', 'total']
		for timer in timer_list:
			print(timer)
			raw = ','.join(["{:.4f}".format(x) for x in tree_records[timer]])

			average = numpy.mean(tree_records[timer])
			std = numpy.std(tree_records[timer])

			print("raw: {}".format(raw))
			print("average: {:.4f}\n".format(average))

			output += "{}\t{:.4f}\t{:.4f}\n".format(timer, average, std)
			tree_records[timer].clear()
		output += '\n'

	with open (res_file, 'w') as f:
		f.write(output)


if __name__ == '__main__':

	if len(argv) != 3:
		print(error)
		print(usage)
	else:
		main(argv[1:])