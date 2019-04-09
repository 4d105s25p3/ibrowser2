#!/usr/bin/python3

import random
import gzip

from sys import argv

error = "Invaild input"
usage = "Usage: sampling.py [option] infile nr_of_sample [outfile]"
options = "Options: --no-random"

def openfile(infile, method, compresslevel=1):
    """
    Open file handling if compressed or not
    """
    fhd = None

    if infile.endswith('.gz'):
        fhd = gzip.open(infile, method, compresslevel)

    else:
        fhd = open(infile, method + '+b')

    return fhd

def main(args):
	if '--' in args[0]: 
		option = args[0]
		args = args[1:]
	else: 
		option = None

	infile = args[0]
	nr_samples = int(args[1])

	if len(args) == 3:
		outfile = args[2]
	else:
		outfile = infile + '.sample'

	nr_all_samples = 0
	samples = []
	with openfile(infile, 'r') as inf:
		with open(outfile, 'w+b') as outf:
			for count, line in enumerate(inf):
				line = line.strip()
				if not line: continue

				if line.startswith(b'#'): # header
					if line.startswith(b'##'): # definition lines
						outf.write(line + b'\n')
					else: # column description
						ls = line.split(b'\t')
						shared = ls[:9]
						sample_names = ls[9:]

						nr_all_samples = len(ls) - 9
						print("Data has {} samples in total.".format(nr_all_samples))
						
						if nr_all_samples < nr_samples:
							print("Number for sampling is {}, larger than number of all samples. Exit.".format(nr_samples))
							exit(1)

						if option == '--no-random':
							samples = list(range(nr_samples))
						else:
							samples = list(range(nr_all_samples))
							samples = random.sample(samples, nr_samples)

						sample_names = [sample_names[i] for i in samples]
						ls = shared + sample_names
						outf.write(b'\t'.join(ls) + b'\n')
				else:
					ls = line.split(b'\t')
					shared = ls[:9]
					data = ls[9:]
					data = [data[i] for i in samples]
					ls = shared + data
					outf.write(b'\t'.join(ls) + b'\n')

				if count % 1000 == 0: 
					if count != 0: 
						print(".", end = '', flush = True)
						if count % 100000 == 0: print("\n{} lines".format(count), flush = True)
			print('\n')



if __name__ == '__main__':

	if len(argv) > 5 or len(argv) < 3:
		print(error)
		print(usage)
		print(options)
		exit(1)

	main(argv[1:])