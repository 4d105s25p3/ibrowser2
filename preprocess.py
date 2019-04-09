#!/usr/bin/python3

import os
import time
import threading

import read_data

from sys import argv
from timer import preprocessing_timer, preprocessing_records
from multiprocessing import Process, Pool, TimeoutError
from threading import Thread


"""
REQUIREMENTS:

Command line tools:
vcf2bed (convert2bed sort-bed) bedGraphtoBigWig bedToBigWig

"""

err = "Invaild input"
usage = """
Usage: preprocess.py [option] [project] [chrom_sizes] [input_VCFs...]
Options: --tabix --bigBed --bigWig --extract
Extra Options: -keep-temp -single-process

Detail usage:
[option]
You must choose one from the four options. Besides, you may combine with extra options.
Examples: --bigBed-keep-temp, --bigWig-single-process.
When using --extract, make sure the name of bigBed file is identical to name of project (like tomato/tomato.bb).
[project]
This is required.
[chrom_sizes]
Required for --tabix, --bigBed and --bigWig mode.
[input_VCFs]
An optional parameter. They should be seperated by space.
If not specified, all VCFs in project folder will be used.
"""
remove_temp_files = True

def print_time(project, processes, accessions = None):
	timer_file = project + "/timer"
	with open(timer_file, "a") as f:
		if accessions:
			f.write("\n{} new accessions added:\n".format(len(accessions)))
			f.write("\t".join(accessions) + "\n")
		f.write("Number Of Processes Used: {}\n".format(processes))
		f.write("Func_Name\tTotal_Time\tProcess_Time\tUser_Time\tSystem_Time\n")
		for record in preprocessing_records:
			f.write("{}\t{:.3f}\t{:.3f}\t{:.3f}\t{:.3f}\n".format(record[0], record[1], record[2], record[3], record[4]))


def rename(name, new, project, suffix, all = False):
	if all: 
		cmd = "rename 's/{}/{}/g' {}/*.{}".format(name, new, project, suffix)
	else:
		cmd = "rename 's/{}/{}/' {}/*.{}".format(name, new, project, suffix)
	print("renaming, cmd: {}".format(cmd))
	os.system(cmd)


@preprocessing_timer
def split_and_filter_vcf(vcf):
	# split vcf file
	os.system("./split_vcf.py {}".format(vcf))

@preprocessing_timer
def decompress_vcf(project, processes = 8):
	# decompress vcf files
	processes = 30
	cmd = "find " + project + "/ -name '*.gz' | sort | xargs -I {{}} -P{} bash -c 'gunzip {{}}'".format(processes)
	print("decompressing gunziped files")
	print("cmd: " + cmd)
	os.system(cmd)

	# rename output
	rename('.gz', '', project, 'vcf')
	rename('.vcf', '', project, 'vcf')


@preprocessing_timer
def run_vcf_to_bed12(project, processes = 8):
	# vcf to bed12
	processes = 30
	cmd = "find " + project + "/ -name '*.vcf' | sort | xargs -I {{}} -P{} bash -c 'vcf2bed -p < {{}} > {{}}.bed12 --do-not-split'".format(processes)
	print("transferring vcf to bed12 format")
	print("cmd: " + cmd)
	os.system(cmd)
	rename('.vcf', '', project, 'bed12')


@preprocessing_timer
def merge_beds(project, in_format = "bed12", out_format = "bed4", append = False):
	# check output format
	support_output = ["bed3", "bed4"]
	if out_format not in support_output:
		raise TypeError("Unknown output format: only bed3 and bed4 are supported")

	# get input, output file names
	bedfiles = os.popen("find {}/ -name '*.{}'".format(project, in_format)).read().strip().split('\n')

	# print task info
	print("merging bed files")
	print("found files: ")
	for bed in bedfiles: print(bed)

	if "/" in project:
		project_name = project.rpartition("/")[2]
	else:
		project_name = project
	outputf = "{}/{}.{}".format(project, project_name, out_format)

	if not append:
		if os.path.exists(outputf):
			print("WARNING: Output file already existed and will be overwritten")
			os.system("rm {}".format(outputf))

	samples = []

	for bed in bedfiles:
		# sample_name = bed.rpartition(".")[0].rpartition("_")[-1] # assumed format: [origrin_name]_[sample_nr]_[sample_name].bed12
		sample_name = bed.rpartition(".")[0].rpartition(".")[-1] # assumed format: [origrin_name].[sample_nr].[sample_name].bed12
		samples.append(sample_name)

		# merge input files to single output file
		if out_format == "bed3":
			cmd = "awk '{{printf \"%s\\t%s\\t%s\\n\", \"{0}_\"$1,$2,$3 >> \"{1}\"}}' {2}".format(sample_name, outputf, bed)
		elif out_format == "bed4":
			cmd = "awk '{{printf \"%s\\t%s\\t%s\\t%s\\n\", \"{0}_\"$1,$2,$3,$7 >> \"{1}\"}}' {2}".format(sample_name, outputf, bed)
		print("merging file {}".format(bed))
		print("sample_name: " + sample_name)
		print(cmd)
		os.system(cmd)

		# remove input file
		if remove_temp_files:
			cmd = "rm {}".format(bed)
			print("removing file")
			print(cmd)
			os.system(cmd)


	# cleaning jobs
	#os.system("rm *.bedgraph")

	return outputf, samples


@preprocessing_timer
def save_data_table(project, chrom_sizes, samples):
	print("generating chromosome list")
	data_table = ""
	with open(chrom_sizes, 'r') as inf:
		for line in inf:
			line = line.strip()
			if line:
				chrom, size = line.split('\t')
				for sample in samples:
					data_table += "{}_{}\t{}\n".format(sample, chrom, size)
	outfile = project + "/data_table"
	with open(outfile, 'w') as outf:
		outf.write(data_table)
	print("chromosome list done")

	return outfile


@preprocessing_timer
def common_workflow(project, chrom_sizes, vcf_inputs = None, processes = 8):
	
	if not vcf_inputs:
		vcf_files = os.popen("find {}/ -name '*.vcf'".format(project)).read().strip().split('\n')
		vcf_gz_files = os.popen("find {}/ -name '*.vcf.gz'".format(project)).read().strip().split('\n')
		vcf_inputs = vcf_files + vcf_gz_files
		if "" in vcf_inputs:
			vcf_inputs.remove("")
		print("Data:\n{}".format('\n'.join(vcf_inputs)))

	print("VCF Inputs: {}".format(vcf_inputs))
	for vcf in vcf_inputs:
		# clean_name = vcf.replace('.gz', '').replace('.vcf', '') # just for rename files
		split_and_filter_vcf(vcf)
		# temporarily rename input file
		os.system("mv {0} {0}.temp".format(vcf))

	decompress_vcf(project, processes = processes)
	run_vcf_to_bed12(project, processes = processes)

	# clean filtered vcf files and list files
	if remove_temp_files:
		remove_file(project, fmt = "lst")
		remove_file(project, fmt = "vcf")
	# restore original name of input files
	rename('.temp', '', project, 'temp')

	# bed4_name = clean_name + '.bed4'
	merged_bed, samples = merge_beds(project)
	data_table = save_data_table(project, chrom_sizes, samples)

	return merged_bed, samples, data_table


""" common workflow ends """
""" for tabix and bigBed """


@preprocessing_timer
def run_command_line_tabix(merged_bed, in_format = "bed4"):
	bed_name = merged_bed.rpartition(".")[0] + "." + in_format
	# compress bed file
	cmd = "bgzip -c {0} > {0}.gz".format(bed_name)
	print("Compressing bed file\ncmd: {}".format(cmd))
	os.system(cmd)
	# make index
	cmd = "tabix -p bed {}.gz".format(bed_name)
	print("Making index\ncmd: {}".format(cmd))
	os.system(cmd)

	return "{}.gz".format(bed_name)
	

@preprocessing_timer
def run_bed_to_bigBed(project, bed, data_table, in_format = "bed4"):
	cmd = "bedToBigBed {0} {1} {0}.bb".format(bed, data_table, bed)
	print("\nMaking bigbed files\ncmd: {}".format(cmd))
	os.system(cmd)

	rename('.{}'.format(in_format), ''.format(in_format), project, 'bb')
	if remove_temp_files:
		remove_file(project, fmt = "bed4")

	return (bed + ".bb").replace('.' + in_format, "")


""" for bigWig """


@preprocessing_timer
def generate_bigWig(data, data_type = "bigBed", processes = 8, refs = None):
	print("{} file: {}".format(data_type, data))
	if data_type == "bigBed":
		d = read_data.BigBed(data)
	elif data_type == "tabix":
		d = read_data.Tabix(data)
	else:
		raise TypeError("Unknown data type")

	print("Making bigWig database")
	d.extract_to_bigWig(processes = processes, refs = refs)


""" End of workflow """


@preprocessing_timer
def finish():
	print("Done")


def remove_file(project, fmt = None):
	if fmt: 
		print("Removing temporary {} files".format(fmt))
		os.system("rm {}/*.{}".format(project, fmt))
	else:
		print("Removing ALL temporary files")
		os.system("rm {}/*.size".format(project))
		os.system("rm {}/*.bed12".format(project))
		os.system("rm {}/*.vcf".format(project))
		os.system("rm {}/*.bedgraph".format(project))
		os.system("rm {}/*.lst".format(project))
		os.system("rm {}/*.bed4".format(project))
		os.system("rm {}/data_table".format(project))


@preprocessing_timer
def main(mode, project, processes = 8, vcf_inputs = None):
	print("mode: " + mode)
	print("Remove temporary files: {}".format(remove_temp_files))

	if mode == "extract":
		project_folder = project.strip("/ ").split("/")[-1]
		bb = "{}/{}.bb".format(project, project_folder)
		generate_bigWig(bb, processes = processes)
		return 0

	merged_bed, samples, data_table = common_workflow(project, chrom_sizes, vcf_inputs = vcf_inputs, processes = processes)

	# --bed4-tabix: merged-bed4 + chrom-list > tabix
	# --bed4-bigBed: merged-bed4 + chrom-list > bigBed
	# --bed3-bigWig: merged-bed4 + chrom-list > merged-bed3 > bedGraph > bigWig

	if mode == "tabix":
		os.system("ls ./{}".format(project))
		print("merged bed file: {}".format(merged_bed))
		tabix = run_command_line_tabix(merged_bed)
	else:
		bb = run_bed_to_bigBed(project, merged_bed, data_table)

	if mode == "bigWig":
		generate_bigWig(bb, processes = processes)

	"""
	if remove_temp_files:
		remove_file(project)
	"""


if __name__ == '__main__':

	if len(argv) >= 3 and len(argv) <= 5:
		option = argv[1]
		project = argv[2]
		if project.endswith('/'): project = project.rstrip('/')

		if "keep-temp" in option:
			remove_temp_files = False

		processes = 8
		if "single-process" in option:
			processes = 1
		elif "multi-process" in option:
			pass # processes = int(args[3])
		
		if "extract" in option:
			main(mode = "extract", project = project, processes = processes)
		else:
			if len(argv) == 3:
				print(err)
				print(usage)
				exit(1)
			chrom_sizes = argv[3]

			vcf_inputs = None
			if len(argv) > 4:
				vcf_inputs = argv[3:]

			if "bigBed" in option:
				mode = "bigBed"
			elif "tabix" in option:
				mode = "tabix"
			elif "bigWig" in option:
				mode = "bigWig"
			else:
				print(err)
				print(usage)
				exit(1)
			main(mode = mode, project = project, processes = processes, vcf_inputs = vcf_inputs)
	else:
		print(err)
		print(usage)
		exit(1)

	print_time(project, processes)