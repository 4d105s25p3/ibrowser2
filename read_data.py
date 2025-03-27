#!/usr/bin/python3

import os
import pandas as pd
import pysam
import pyBigWig

from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceTreeConstructor, _DistanceMatrix

from io import StringIO
from timer import tree_timer, test_timer
from multiprocessing import Pool, Manager


def _compare_samples(data, ref_data):
		# assumed format: data = [(1000, 'A'), (1205, 'T'), ...]
		data = set(data)
		ref_data = set(ref_data)

		new_data = list(dict(data-ref_data|ref_data-data).keys())
		new_data.sort()

		return new_data

def _to_bigWig(task_nr, res_dict, project, file, chroms, ref, samples, bedGraphf, sizef):
	
	def _bigBed_parser(bigBed, name, start, end):
		data = list(bigBed.entries(name, start-1, end))
		if data: data = [(x[1], x[2]) for x in data]
		return data

	
	vaild_samples = list(samples)

	try:
		print("Process for ref: {}, samples: {}".format(ref, vaild_samples))
		for chrom in chroms:
			chromLength = chroms[chrom]
			
			sizes = []
			with open(bedGraphf, 'a') as f:
				bb = 0
				for count, sample in enumerate(samples):
					if ref == sample: 
						if sample in vaild_samples:
							vaild_samples.remove(sample)
						continue

					sample_name = sample + '_' + chrom
					ref_name = ref + '_' + chrom
					bb = pyBigWig.open(file)

					if ref == 'ref' or sample == 'ref':
						if sample == 'ref':
							data = _bigBed_parser(bb, ref_name, 1, chromLength)
						else:
							data = _bigBed_parser(bb, sample_name, 1, chromLength)
						for item in data:
							f.write("{}\t{}\t{}\t1\n".format(sample_name, item[0]-1, item[0]))
					else:
						ref_data = _bigBed_parser(bb, ref_name, 1, chromLength)
						sample_data = _bigBed_parser(bb, sample_name, 1, chromLength)
						new_data = _compare_samples(ref_data, sample_data)
						new_data.sort()
						for pos in new_data:
							f.write("{}\t{}\t{}\t1\n".format(sample_name, pos - 1, pos))
					# print(".", end = "", flush = True)
					sizes.append("{}\t{}\n".format(sample_name, chromLength))

			if bb:
				with open(sizef, 'a') as f:
					for line in sizes:
						f.write(line)
				print("....bedGraph Extracted: Sample {} Chrom {}".format(ref, chrom))
				hasData = 1
			else:
				print("....bedGraph Skipped: Sample {} Chrom {}".format(ref, chrom))

		if vaild_samples:
			cmd = "bedGraphToBigWig {0}.bedgraph {0}.size {0}.bw".format(project + '/' + ref)
			os.system(cmd)			
			print("****Task {} for Sample {} Done.".format(task_nr, ref))
		else:
			print("****Task {} for Sample {} Skipped.".format(task_nr, ref))	

		cmd = "rm {0}.size {0}.bedgraph".format(project + '/' + ref)
		os.system(cmd)

		res_dict[ref] = len(vaild_samples)
		return len(vaild_samples)

	except OSError:
		print("OSError Encountered in Process for ref: {}, samples: {}.\nIt could be intermediate files that run out of disk space.\nBigWig file will be removed".format(ref, vaild_samples))
		cmd = "rm {}.bw".format(project + '/' + ref)
		os.system(cmd)
		return 0


def _get_bigWig(res_dict, samplesForProcess, chrom, nBins, start, end):
	#print("Dataset: {}".format(samplesForProcess))
	for item in samplesForProcess:
		print("real sample: {}, sample will be used: {} ref file: {}".format(item[0], item[1], item[2]))

		name = item[1] + "_" + chrom # used for query, format: sample_chrom. It is the sample that used for query instead of real sample

		bw = pyBigWig.open(item[2])
		#print(bw)
		#print("name: {}, start: {}, end: {}, nBins: {}".format(name, start-1, end, nBins))
		data = bw.stats(name, start-1, end, type = "coverage", nBins = nBins)
		data = [x if x else 0.0 for x in data]
		#print(data)

		res_dict[item[0]] = data



def _res_format_converter(res_dict, samples, return_format):
	if return_format == "list":
		res_list = []
		for sample in samples:
			res_list.append(res_dict[sample])
		return res_list
	elif return_format == "json":
		res_list = []
		for sample in samples:
			res_list.append({
				"sample": sample,
				"data": res_dict[sample]
				})
		return res_list
	else:
		return res_dict


class Data(object):
	counter = 0

	def __init__(self, data_file = None, index_file = None):
		self._data_file = data_file
		self._index_file = index_file
		self._project = self._data_file.rpartition("/")[0]
		self._data = None

		self._ref = None
		self._samples = []
		self._chroms = {}
		self._data_table = {}

	@property
	def data_file(self):
		return self._data_file

	@property
	def index_file(self):
		return self._index_file

	@property
	def project(self):
		return self._project
	
	
	@property
	def samples(self):
		return self._samples

	@property
	def available_samples(self):
		samples = list(self._samples)
		samples.remove(self._ref)
		return set(samples)
	
	@property
	def chromosomes(self):
		return set(self._chroms.keys())
		
	@property
	def chroms(self):
		return self._chroms
	
	@property
	def data_table(self):
		return self._data_table

	@property
	def ref(self):
		return self._ref

	def get_data_matrix(self):
		data_matrix = {}
		for chrom in self.chroms:
			data_matrix[chrom] = pd.DataFrame(index = self.samples, columns = self.samples)
		return data_matrix

	def switch_ref(self, new_ref):
		if new_ref not in self.samples:
			raise ValueError('new reference not found in data!')
		else:
			self._ref = new_ref

	def _get_data(self, name, start, end):
		return None

	def _get_bed4(self, chrom, sample, start, end, nBins):
		length = end - start + 1
		step = length // nBins
		bin_list = [step] * nBins

		reminder = length % nBins
		for i in range(reminder): bin_list[i] += 1

		if sample == 'ref':
			name = "{}_{}".format(self._ref, chrom)
		else:
			name = "{}_{}".format(sample, chrom)

		data = self._get_data(name, start, end)

		if self.ref == 'ref' or sample == 'ref': # current_ref is 'ref' or current_ref is not 'ref' but data is 'ref'
			if not data: return [0.0] * nBins # data is empty, so data = 'ref'
			res = self.__get_coverage(data, nBins, start, bin_list)

		else: # current_ref is not 'ref', however only information between data and 'ref' is stored, so more comparison is needed
			ref_name = "{}_{}".format(self.ref, chrom)
			ref_data = self._get_data(ref_name, start, end)

			if not data:
				if not ref_data: return [0.0] * nBins # both sets are empty, data = 'ref' = current_ref
				res = self.__get_coverage(ref_data, nBins, start, bin_list) # data = 'ref', only need to compare between current_ref and 'ref'
			elif not ref_data:
				res = self.__get_coverage(data, nBins, start, bin_list) # current_ref = 'ref', only need to compare between data and 'ref'
			else:
				new_data = _compare_samples(data, ref_data) # need to compare 'ref', data and current_ref
				if not new_data: 
					res = [0.0] * nBins
				else:
					res = self.__get_coverage(new_data, nBins, start, bin_list)
		return res

	def __get_coverage(self, data, nBins, start, bin_list):
		try:
			data = [x[0] for x in data] # remove alt
		except TypeError:
			pass # if data is new data then there is no alt
		res = [0.0] * nBins
		i = 0 # index of bins
		j = 0 # index of SNPs
		bin_start = start
		bin_end = bin_start + bin_list[i]
		
		while j < len(data):
			if data[j] >= bin_start and data[j] < bin_end:
				res[i] += 1 # No.i bin +1 count
				j += 1 # next SNP
			else: 
				i += 1 # next bin
				bin_start = bin_end
				bin_end = bin_start + bin_list[i]

		coverage = [res[i]/bin_list[i] for i in range(nBins)]
		return coverage

	def _compare_samples(data, ref_data):
		# assumed format: data = [(1000, 'A'), (1205, 'T'), ...]
		data = set(data)
		ref_data = set(ref_data)

		new_data = list(dict(data-ref_data|ref_data-data).keys())
		new_data.sort()

		return new_data

	def _check_input(self, nBins, chrom, samples, start, end):
		if chrom not in self.data_table.keys():
			raise ValueError("Chromosome not found")

		else:
			old_nBins = nBins
			for sample in samples:
				if sample == self._ref:
					# print("WARNING: sample {} is current reference sample".format(sample))
					pass
				elif sample not in self._data_table[chrom]:
					raise ValueError("No data for sample {} in chromosome {}".format(sample, chrom))

				if not end: end = self.chroms[chrom]
				if start > end: raise ValueError("Start pos should not exceed end pos!")
				if start < 1: raise ValueError("1-base format: position values should between 1 and length of chromosome!")

				if nBins > end - start + 1: 
					nBins = end - start + 1

			if old_nBins != nBins:
				print("WARNING: The number of blocks is greater than length of target chromosome region")
				print("Number of blocks has been reduced to {}".format(nBins))

		return nBins, chrom, samples, start, end

	def _to_csv_format(self, res_table):
		res_str = ''
		for item in res_table:
			res_str += item + ','
			res_str += ','.join([str(x) for x in res_table[item]])
			res_str += '\n'
		return res_str


	@test_timer
	def extract_to_bigWig(self, processes = 8, refs = None):
		if not refs: # build from bigBed database for the first time, use all inner samples as references
			refs = list(self.samples)
		nr_refs = len(refs)
		samples = list(self.samples)

		if processes > 1:
			print("Running multi-process extract method")
			manager = Manager()
			res_dict = manager.dict()
			pool = Pool(processes = processes)
			for i in range(nr_refs):
				ref = refs[i]
				bedGraphf =  "{}/{}.bedgraph".format(self.project, ref)
				bedGraphf = os.path.abspath(bedGraphf)

				sizef = "{}/{}.size".format(self.project, ref)
				sizef = os.path.abspath(sizef)

				print("iteration: {}, ref: {}, samples: {}".format(i, ref, samples))
				idx = pool.apply_async(_to_bigWig, [i, res_dict, self.project, self._data_file, self.chroms, ref, list(samples), bedGraphf, sizef])

				if ref in samples:
					samples.remove(ref)
					print("ref {} removed".format(ref))
			pool.close()
			pool.join()
			res_dict = dict(res_dict)

		elif processes == 1:
			print("Running single-process extract method")
			res_dict = {}
			for i in range(nr_refs):
				ref = refs[i]
				bedGraphf =  "{}/{}.bedgraph".format(self.project, ref)
				bedGraphf = os.path.abspath(bedGraphf)

				sizef = "{}/{}.size".format(self.project, ref)
				sizef = os.path.abspath(sizef)

				print("iteration: {}, ref: {}, samples: {}".format(i, ref, samples))
				idx = _to_bigWig(res_dict, self.project, self._data_file, self.chroms, ref, list(samples), bedGraphf, sizef)

				if ref in samples:
					samples.remove(ref)
					print("ref {} removed".format(ref))

		
		# Make new indexes from apply results
		print(res_dict)
		new_indexes = {}
		for ref in res_dict:
			if res_dict[ref] in new_indexes:
				print("idx: {}".format(res_dict[ref]))
				print("dict: {}".format(new_indexes))
				raise ValueError("Repeted Index Found! Some References Might Be Duplicated")
			if res_dict[ref] > 0:
				new_indexes[res_dict[ref]] = "{0}\t{0}.bw\n".format(ref)
			else:
				new_indexes[res_dict[ref]] = "{}\t\n".format(ref)

		# Read all old indexes
		bw_index = self.project + "/index"
		print(bw_index)
		old_indexes = {}
		if os.path.exists(bw_index):
			with open(bw_index, "r") as idf:
				for line in idf:
					if not line.strip(): continue
					line_list = line.partition("\t")
					old_indexes[int(line_list[0])] = line_list[2]

		# Mix old and new indexes and sort them
		new_keys = list(old_indexes.keys()) + list(new_indexes.keys())
		new_keys.sort()
		if len(new_keys) != len(set(new_keys)):
			print("Error Message, New keys:\n{}".format(new_keys))
			raise ValueError("Repeted Index Found! Some References Might Be Duplicated")
		indexes = {}
		for key in new_keys:
			if key in old_indexes:
				indexes[key] = old_indexes[key]
			else:
				indexes[key] = new_indexes[key]

		# Write mixed and sorted indexes to file
		with open(bw_index, "w") as idf:
			for key in new_keys:
				idf.write("{}\t{}".format(key, indexes[key]))
		
		return refs


	"""
	@test_timer
	def extract_bed4_to_bedGraph(self, folder = '.', refs = None):

		samples = list(self.samples)
		if not refs:
			nr_refs = len(samples)
		else:
			nr_refs = len(refs)
		nr_pairs = int(nr_refs*(nr_refs-1))
		
		for i in range(nr_refs):
			if not refs:
				ref = samples[i]
			else:
				ref = refs[i]

			bedGraphf =  "{}/{}.bedgraph".format(folder, ref)
			bedGraphf = os.path.abspath(bedGraphf)

			sizef = "{}/{}.size".format(folder, ref)
			sizef = os.path.abspath(sizef)

			sizes = []

			print("\n###### Reference {}/{}: {} ######".format(i+1, nr_refs, ref), flush = True)
			with open(bedGraphf, 'w') as f:
				chroms = list(self.data_table.keys())
				for chrom in chroms:
					print("\n****** Chromsome {} ******".format(chrom))
					end = self.chroms[chrom]

					for count, sample in enumerate(samples):
						if ref == sample: continue
						
						sample_name = sample + '_' + chrom
						ref_name = ref + '_' + chrom

						sizes.append("{}\t{}\n".format(sample_name, end))

						if sample == 'ref':
							data = self._get_data(ref_name, 1, end)
						elif ref == 'ref':
							data = self._get_data(sample_name, 1, end)

						if ref == 'ref' or sample == 'ref':
							for item in data:
								f.write("{}\t{}\t{}\t1\n".format(sample_name, item[0]-1, item[0]))
						else:
							ref_data = self._get_data(ref_name, 1, end)
							sample_data = self._get_data(sample_name, 1, end)
							new_data = _compare_samples(ref_data, sample_data)
							new_data.sort()

							for pos in new_data:
								f.write("{}\t{}\t{}\t1\n".format(sample_name, pos - 1, pos))
						print(".", end = "", flush = True)
					print("\n")
				print("\n")

			with open(sizef, 'w') as f:
				for line in sizes:
					f.write(line)

			yield ref, bedGraphf, sizef

		print('\n')
			

	def extract_bed4_to_bedGraph_old(self, *args, **kwds):

		bedGraphf_table = {}
		sizef_table = {}

		for ref, bedGraphf, sizef in self.extract_bed4_to_bedGraph(*args, **kwds):
			bedGraphf_table[ref] = bedGraphf
			sizef_table[ref] = sizef

		return bedGraphf_table, sizef_table
	"""


class Tabix(Data):

	def __init__(self, data_file, index_file = None):
		if not index_file:
			index_file = data_file + ".tbi"
			if not os.path.exists(chrom_file):
				raise IOError("Tabix file not found")
		super(Tabix, self).__init__(data_file, index_file)

		self._data = pysam.TabixFile(self.data_file)
		self._ref = 'ref'
		self._samples.append('ref')
		with open(self._index_file, 'r') as f:
			for line in f:
				line = line.strip()
				if not line: continue

				name, size = line.split('\t')
				size = int(size)
				sample, chrom = name.split('_')

				self._samples.append(sample)
				if chrom not in self._chroms:
					self._chroms[chrom] = 0
				self._chroms[chrom] = max(self._chroms[chrom], size)

				if chrom not in self._data_table: 
					self._data_table[chrom] = {}
				self._data_table[chrom][sample] = size
		self._samples = set(self._samples)

		for chrom in self._data_table:
			self._data_table[chrom]['ref'] = self._chroms[chrom]

	def _get_data(self, name, start, end):
		data = list(self._data.fetch(name, start-1, end))
		if data: data = [(int(x.split('\t')[2]), x.split('\t')[3]) for x in data]
		return data

	@test_timer
	def get(self, nBins, chrom, samples, start = 1, end = None, return_format = "table"): # 1-base pos format
		nBins, chrom, samples, start, end = self._check_input(nBins, chrom, samples, start, end)

		res_table = {}
		for sample in samples:
			if sample == self.ref: 
				res = [0.0] * nBins
			else:
				res = self._get_bed4(chrom, sample, start, end, nBins)
			res_table[sample + '_' + chrom] = res

		if return_format == "csv":
			return self._to_csv_format(res_table)
		else:
			return res_table
		

class Big(Data):

	def __init__(self, data_file, ref = 'ref'):
		super(Big, self).__init__(data_file, index_file = None)
		
		print("Opening file: " + self.data_file)
		self._data = pyBigWig.open(self.data_file)
		self._ref = ref
		self._samples.append(ref)

		for item in self._data.chroms():
			sample, chrom = item.split('_')
			size = self._data.chroms()[item]

			self._samples.append(sample)
			if chrom not in self._chroms:
				self._chroms[chrom] = 0
			self._chroms[chrom] = max(self._chroms[chrom], size)

			if chrom not in self._data_table: 
				self._data_table[chrom] = {}
			self._data_table[chrom][sample] = size
		self._samples = set(self._samples)

		for chrom in self._data_table:
			self._data_table[chrom]['ref'] = self._chroms[chrom]

	@property
	def index_file(self):
		raise ValueError("Big file has no index file!")
		return None


class BigBed(Big):
	def __init__(self, data_file):
		super(BigBed, self).__init__(data_file)

	def _get_data(self, name, start, end):
		data = list(self._data.entries(name, start-1, end))
		if data: data = [(x[1], x[2]) for x in data]
		return data

	@test_timer
	def get(self, nBins, chrom, samples, start = 1, end = None, return_format = "table"): # 1-base pos format
		nBins, chrom, samples, start, end = self._check_input(nBins, chrom, samples, start, end)

		res_table = {}
		for sample in samples:
			if sample == self.ref: 
				res = [0.0] * nBins
			else:
				res = self._get_bed4(chrom, sample, start, end, nBins)
			res_table[sample + '_' + chrom] = res

		if return_format == "csv":
			return self._to_csv_format(res_table)
		else:
			return res_table


class BWData(Big):
	def __init__(self, data_file, ref = None):
		if not ref:
			ref = data_file.split('.')[0]

		super(BWData, self).__init__(data_file, ref)

	def __get_wig(self, nBins, chrom, sample, start, end):
		name = sample + '_' + chrom
		data = self._data.stats(name, start-1, end, type = "coverage", nBins = nBins)
		data = [x if x else 0.0 for x in data]

		return data

	def switch_ref(self):
		raise TypeError("BWData object does not support reference switching")

	def get(self, nBins, chrom, samples, start = 1, end = None, return_format = "table"): # 1-base pos format

		res_table = {}
		res_list = []
		for sample in samples:
			if sample == self.ref: 
				res = [0.0] * nBins
			else:
				res = self. __get_wig(nBins, chrom, sample, start, end)
			res_table[sample + '_' + chrom] = res
			res_list.append(res)

		if return_format == "list":
			return res_list
		elif return_format == "csv":
			return self._to_csv_format(res_table)
		else:
			return res_table




			
class BigWig(object):
	def __init__(self, index_file):
		self._index_file = index_file
		self._sample_table = {}
		self._file_table = {}
		self._bw_table = {}
		self._chroms = {}
		self._folder = self._index_file.rpartition('/')[0] + '/'
		self._current_ref = None
		self._current_ref_idx = -1

		with open(index_file, 'r') as idf:
			for line in idf:
				line = line.strip()
				if not line: continue

				line_list = line.split("\t")
				if len(line_list) == 3:
					idx, sample, path = line_list
				else:
					idx, sample = line_list
					path = ""

				""" JUST A PATCH """
				""" replace ".bed3" in index file with ".bw" """
				""" path = path.rpartition(".")[0] + '.bw' """
				if path:
					path = self._folder + path
				if sample not in self._file_table:
					self._sample_table[sample] = int(idx)
					self._file_table[sample] = path

		self._load_all_data()
		self.switch_ref('ref')
		self._set_chroms()

	@property
	def index_file(self):
		return self._index_file

	@property
	def sample_table(self):
		return self._sample_table

	@property
	def file_table(self):
		return self._file_table
	
	@property
	def ref(self):
		return self._current_ref

	@property
	def current_ref_idx(self):
		return self._current_ref_idx
	

	@property
	def samples(self):
		return set(self.sample_table.keys())
	
	@property
	def available_samples(self):
		samples = list(self.samples)
		samples.remove(self.ref)
		return samples

	@property
	def chroms(self):
		return self._chroms
	
	@property
	def available_chroms(self):
		return list(self._bw_table[self.ref].chromosomes)
	
	@property
	def bw_table(self):
		return self._bw_table

	def _load_all_data(self):
		for sample in self.sample_table:
			if self.file_table[sample]:
				self._bw_table[sample] = BWData(self.file_table[sample], sample)
				chroms = self.bw_table[sample].chroms
				for chrom in chroms:
					if chrom not in self._chroms:
						self._chroms[chrom] = chroms[chrom]
					else:
						self._chroms[chrom] = max(self.chroms[chrom], chroms[chrom])
			else:
				self._bw_table[sample] = None

	def _set_chroms(self):
		for ref in self.bw_table:
			if not self.bw_table[ref]: continue
			chroms = self.bw_table[ref].chroms
			for chrom in chroms:
				if chrom not in self.chroms:
					self._chroms[chrom] = chroms[chrom]
				else:
					self._chroms[chrom] = max(self.chroms[chrom], chroms[chrom])

	def _check_input(self, nBins, chrom, samples, start, end):
		if chrom not in self.chroms.keys():
			raise ValueError("Chromosome not found")
		if start < 1: 
			raise ValueError("1-base format: position values should between 1 and length of chromosome!")

		old_nBins = nBins
		for sample in samples:
			if sample == self.ref:
				# print("WARNING: sample {} is current reference sample".format(sample))
				pass

			if not end: end = self.chroms[chrom]
			if start > end: raise ValueError("Start pos should not exceed end pos!")
			if nBins > end - start + 1: 
				nBins = end - start + 1

		if old_nBins != nBins:
			print("WARNING: The number of blocks is greater than length of target chromosome region")
			print("Number of blocks has been reduced to {}".format(nBins))

		return nBins, chrom, samples, start, end

	def switch_ref(self, new_ref):
		if new_ref not in self.sample_table:
			raise ValueError("Sample {} not found in data!".format(new_ref))
		if new_ref not in self._bw_table:
			print(new_ref)
			print(self.bw_table)
			print(self.sample_table)
			if self.file_table[new_ref]:
				self._bw_table[new_ref] = BWData(self.file_table[new_ref], new_ref)
			else:
				self._bw_table[new_ref] = None
		self._current_ref = new_ref
		self._current_ref_idx = self.sample_table[new_ref]

	@test_timer
	def get_singleprocess(self, nBins, chrom, samples, start = 1, end = None, return_format = "table"):
		nBins, chrom, samples, start, end = self._check_input(nBins, chrom, samples, start, end)



		res_dict = self.bw_table[self.ref].get(nBins, chrom, samples, start, end, return_format)

		return _res_format_converter(res_dict, samples, return_format)

	@test_timer
	def get(self, nBins, chrom, samples, start = 1, end = None, return_format = "table", processes = 8):
		"""return: {sample1: [bin1, bin2, bin3...], sample2: [bin1, bin2, bin3...], sample3...}"""
		nBins, chrom, samples, start, end = self._check_input(nBins, chrom, samples, start, end)
		numOfSamples = len(samples)
		
		if processes > 1:
			manager = Manager()
			res_dict = manager.dict()
			pool = Pool(processes = processes)
			print("Running multi-process get method")
			numOfSamplesPerProcess = numOfSamples // processes + 1

			# record "real" samples, samples that used to get data and ref file names
			# format: [(real_sample1, sample1, ref_file1), (real_sample2, sample2, ref_file2), ...)]
			samplesForProcess = []
			
			for sample in samples:
				if sample == self.ref:
					res_dict[sample] = [0.0] * nBins
					continue
				idx = self.sample_table[sample]
				if idx < self.current_ref_idx:
					samplesForProcess.append((sample, sample, self.bw_table[self.ref].data_file))
				else:
					samplesForProcess.append((sample, self.ref, self.bw_table[sample].data_file))

				if len(samplesForProcess) >= numOfSamplesPerProcess:
					res = pool.apply_async(_get_bigWig, [res_dict, samplesForProcess, chrom, nBins, start, end])
					samplesForProcess = []
				else: 
					continue

			if samplesForProcess:
				res = pool.apply_async(_get_bigWig, [res_dict, samplesForProcess, chrom, nBins, start, end])
				samplesForProcess = []

			pool.close()
			pool.join()

			res_dict = dict(res_dict)
		elif processes == 1:
			print("Running single-process get method")
			res_dict = {}
			for sample in samples:
				if sample == self.ref:
					res_dict[sample] = [0.0] * nBins
					continue
				idx = self.sample_table[sample]
				if idx < self.current_ref_idx:
					samplesForProcess = [(sample, sample, self.bw_table[self.ref].data_file)]
					_get_bigWig(res_dict, samplesForProcess, chrom, nBins, start, end)
				else:
					samplesForProcess = [(sample, self.ref, self.bw_table[sample].data_file)]
					_get_bigWig(res_dict, samplesForProcess, chrom, nBins, start, end)

		return _res_format_converter(res_dict, samples, return_format)

		"""
		if return_format == "list":
			res_list = []
			for sample in samples:
				res_list.append(res_dict[sample])
			return res_list
		elif return_format == "json":
			res_list = []
			for sample in samples:
				res_list.append({
					"sample": sample,
					"data": res_dict[sample]
					})
			return res_list
		else:
			return dict(res_dict)
		"""


	def get_matrix(self, chrom, start = 1, end = None, samples = None, return_format = "matrix"):
		if not samples: 
			samples = self.samples
		samples = list(samples)
		current_ref = self.ref

		print("Getting matrix")
		print("samples: {}".format(samples))
		
		if return_format == "Phylo":
			""" return a list of names and a nested list of numbers in lower triangular matrix format, 
			which can be accepted by Phylo module (from Biopython) to make phylogenetic trees
			"""
			names = []
			matrix = []
			for i in range(len(samples)):
				ref_sample = samples[i]
				data_samples = samples[:i+1]
				print("Processing sample: {}".format(ref_sample))
				self.switch_ref(ref_sample)

				names.append(ref_sample)
				matrix.append([x[0] for x in self.get(1, chrom, data_samples, start, end, return_format = "list")])

			self.switch_ref(current_ref)

			print("Names: {}\nMatrix:\n{}\n".format(names, matrix))
			return names, matrix

		elif return_format == "matrix":
			""" return a pandas.DataFrame object """
			matrix = pd.DataFrame(index = samples, columns = samples)
			for sample in samples:
				self.switch_ref(sample)
				distance = [x[0] for x in self.get(1, chrom, samples, start, end, return_format = "list")]
				matrix.loc[sample] = distance

			self.switch_ref(current_ref)
			return matrix

	@tree_timer
	def get_tree(self, chrom, start = 1, end = None, samples = None, return_format = "tree_obj"):

		print("chrom: {} start: {} end: {} samples: {}".format(chrom, start, end, samples))
		names, matrix = self.get_matrix(chrom, start = start, end = end, samples = samples, return_format = "Phylo")
		distance_matrix = _DistanceMatrix(names, matrix)

		constructor = DistanceTreeConstructor()
		tree = constructor.nj(distance_matrix) # neighbour joining tree

		if return_format == "tree_obj":
			return tree
		elif return_format == "newick":
			treeIO = StringIO()
			Phylo.write(tree, treeIO, "newick")
			treeString = treeIO.getvalue()
			treeString = treeString.strip()
			return treeString
