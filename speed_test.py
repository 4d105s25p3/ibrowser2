#!/usr/bin/python3

import time
import random
import numpy

import read_data as rd

from timer import test_records, test_timer
from sys import argv

error = "Invaild input, see usage below"
usage = "Usage: speed_test.py [option] fileType dataFile testFile [dataTable]"
option_list = "Options: --best-chrom --P[number of process]"
error_file_type = "Unknown file type"
file_type = "Support File Type: --tabix --bigBed --bigWig. Data table file must be provided at last if type is tabix"


def main(args):
	if args[1].startswith('--'):
		options = args[0].strip().split("--")
		print(options)
		args = args[1:]
	else:
		options = []

	data_type, data_file, test_file = args[:3]

	num_of_process = 1
	if options:
		for option in options:
			if "P" in option:
				num_of_process = int(option.partition("=")[2])
				if num_of_process > 1 and data_type != "--bigWig": 
					print("Error: Only bigWig format supports multi-process mode!")
					exit(1)

	data_table = None
	if data_type == '--tabix': 
		data_table = args[3]

	tests = []
	with open(test_file, 'r') as inf:
		inf.readline()
		for line in inf:
			line = line.strip()
			if not line: continue
			items = line.split('\t')
			test = {'nSamples': int(items[0]), 'Length': int(items[1]), 'nBlocks': int(items[2]), 'Ref': items[3], 'Times': int(items[4])}
			tests.append(test)

	test_folder = test_file.rpartition('/')[0]
	test_file_name = test_file.rpartition('/')[2]
	res_file = test_folder + '/' + test_file_name.replace(".test", "") + '.result'
	
	for i in tests: print(i)

	if data_type == '--tabix':
		data = rd.Tabix(data_file, data_table)
	elif data_type == '--bigBed':
		data = rd.BigBed(data_file)
	elif data_type == '--bigWig':
		data = rd.BigWig(data_file)
	else:
		print(error_file_type)
		print(file_type)
		exit(1)
		
	chrom_sizes = data.chroms

	output = "Test for Database: {}\nTest Options: {} {}\n\n".format(data_file, data_type, " ".join(options))
	for test in tests:
		data.switch_ref(test['Ref'])
		for i in range(test['Times']):

			if "best-chrom" in options:
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
				print("WARNING: Length of target sequence has been cut to {}".format(test['Length']))

			start = random.randrange(1, len_chrom - test['Length'] + 2)
			end = start + test['Length'] - 1

			if data_type == "--bigWig":
				temp = data.get(test['nBlocks'], chrom, samples, start = start, end = end, processes = num_of_process)
				# temp = another_test_timer(data.get_singleprocess, test['nBlocks'], chrom, samples, start = start, end = end)
			else:
				temp = data.get(test['nBlocks'], chrom, samples, start = start, end = end)
				# temp = another_test_timer(data.get, test['nBlocks'], chrom, samples, start = start, end = end)

		condition = "nSamples {} Length {} nBlocks {} Ref {} Times {}\n".format(test['nSamples'], test['Length'], test['nBlocks'], test['Ref'], test['Times'])
		output += condition
		output += "timer\tAverage\tStd\n"

		print("\nResults for Test Condition: \n{}\n".format(test))

		timer_list = ['sys', 'user', 'process', 'total']
		for timer in timer_list:
			print(timer)
			raw = ','.join(["{:.4f}".format(x) for x in test_records[timer]])

			average = numpy.mean(test_records[timer])
			std = numpy.std(test_records[timer])

			print("raw: {}".format(raw))
			print("average: {:.4f}\n".format(average))

			output += "{}\t{:.4f}\t{:.4f}\n".format(timer, average, std)
			test_records[timer].clear()
		output += '\n'

	with open (res_file, 'w') as f:
		f.write(output)


if __name__ == '__main__':

	if len(argv) > 6 or len(argv) < 4:
		print(error)
		print(usage)
		print(option_list)
		print(file_type)
	else:
		main(argv[1:])