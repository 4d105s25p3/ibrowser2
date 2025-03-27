#!/usr/bin/python3

import os
import sys

import read_data
import preprocess

from timer import preprocessing_timer, preprocessing_records

err = "Invaild input"
usage = "add_sample.py project bigBed [bw_index]"

@preprocessing_timer
def main(project, bigBed, bw_index):
	preprocess.remove_temp_files = False

	bb = read_data.BigBed(bigBed)
	old_samples = bb.samples

	# extract chrom sizes data from old database and save it to file
	chrom_sizes = project + '/chroms'
	with open(chrom_sizes, 'w') as f:
		for chrom in bb.chroms:
			f.write("{}\t{}\n".format(chrom, bb.chroms[chrom]))

	# generate new bed4 files using new samples and chrom sizes file
	new_bed4, new_samples, new_data_table = preprocess.common_workflow(project, chrom_sizes, processes = 8)
	print(new_bed4)

	# remove temporory vcf and bed12 files
	preprocess.remove_file(project, "vcf")
	preprocess.remove_file(project, "bed12")

	# extract data table from old database
	old_data_table = ""
	for chrom in bb.data_table:
		for sample in bb.data_table[chrom]:
			old_data_table += "{}_{}\t{}\n".format(sample, chrom, bb.data_table[chrom][sample])

	# extract bed4 files from old database
	print("Extracting Old data to bed4 format")
	cmd = "bigBedToBed {} {}".format(bigBed, bigBed + ".bed4")
	print(cmd)
	os.system(cmd)

	# merge new and old bed4 files
	merged_bed4 = project + "/merged.bed4"
	bed4_files = os.popen("find {}/ -name '*.bed4'".format(project)).read().strip().split('\n')
	print("Found bed files:\n{}\n".format("\n".join(bed4_files)))
	print(len(bed4_files))
	for bed4 in bed4_files:
		print("Hello")
		cmd = "awk '{{printf \"%s\\t%s\\t%s\\t%s\\n\", $1,$2,$3,$4 >> \"{0}\"}}' {1}".format(merged_bed4, bed4)
		print("cmd: " + cmd)
		os.system(cmd)

	# sort merged bed4 files
	print("Sorting merged bed4")
	sorted_bed4 = project + "/sorted.bed4"
	cmd = "sort -k1,1 -k2,2n {} > {}".format(merged_bed4, sorted_bed4)
	os.system(cmd)

	# merge new and old data tables
	print("Merging data table")
	with open(new_data_table, 'a') as dt:
		dt.write(old_data_table)

	# rename old dataset
	os.system("mv {0} {0}.old".format(bigBed))

	# rebuild new bigBed dataset
	new_bigBed = preprocess.run_bed_to_bigBed(project, sorted_bed4, new_data_table, in_format = "bed4")
	os.system("mv {} {}".format(new_bigBed, bigBed))
	new_bigBed = bigBed

	# create new bigWig files
	preprocess.generate_bigWig(new_bigBed, refs = new_samples)

	"""	
	# extract new bed3 files from new bigBed dataset
	new_bb = read_data.BigBed(new_bigBed)
	bedGraphf_table, sizef_table = new_bb.extract_bed4_to_bedGraph(project, refs = new_samples)


	# transfrom new bed3 files into bigWig, and add them to index
	preprocess.run_bed_graph_to_bigwig(project)
	

	# write index
	with open(bw_index, 'a') as f:
		for ref in new_refs:
			print("Done: Adding new sample " + ref)
			f.write("{}\t{}\n".format(ref, ref + '.bw'))
	"""

	preprocess.remove_file(project)

	return new_samples


if __name__ == '__main__':

	if len(sys.argv) < 3 or len(sys.argv) > 4:
		print(err)
		print(usage)
		exit(1)

	project = sys.argv[1]
	if project.endswith('/'): project = project.rstrip('/')

	bigBed = sys.argv[2]

	if len(sys.argv) == 4:
		bw_index = sys.argv[2]
	else: # output not specified, use default value
		bw_index = project + '/index'

	new_samples = main(project, bigBed, bw_index)

	preprocess.print_time(project, processes = 8, accessions = new_samples)
	print(preprocessing_records)