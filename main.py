#!/usr/bin/python3

import os
import time
import read_data

from sys import argv
from flask import Flask, url_for, request, redirect, jsonify

supported_format = "tabix-bed4, bigBed, bigWig"
data = {}
tabix = {}
data_sets = {}

for root, dirs, files in os.walk('./data', topdown = True):
	project = root.rpartition('/')[2]
	print("project: {}\tdirs: {}\tfiles: {}\t\n".format(project, dirs, files))
	tabix = {}

	## find data files
	## bigWig: index
	## bigBed: .bb/.bigBed
	## tabix: chroms .gz .gz.tbi
	for file in files:
		if file == 'index':
			data_sets[project] = {'type': 'bigWig', 'data': os.path.join(root, file)}
			break # bigWig has the highest priority

		elif file.endswith('.bb') or file.endswith('.bigBed'):
			if project in data_sets.keys(): raise ValueError("more than one bigBed files")
			data_sets[project] = {'type': 'bigBed', 'data': os.path.join(root, file)}

		elif file == 'chroms': 
			tabix['chroms'] = os.path.join(root, file)
		elif file.endswith('bed4.gz.tbi'):
			if 'index' in tabix.keys(): raise ValueError("more than one index files")
			tabix['index'] = os.path.join(root, file)
		elif file.endswith('bed4.gz'):
			if 'data' in tabix.keys(): raise ValueError("more than one data files")
			tabix['data'] = os.path.join(root, file)

	if project in data_sets.keys():
		continue
	if set(tabix.keys()) == {'index', 'data', 'chroms'}:
		data_sets[project] = {'type': 'tabix', 'chroms': tabix['chroms'], 'tabix': tabix['index'], 'data': tabix['data']}

print(data_sets)

def to_csv_format(res_table):
		res_str = ''
		for item in res_table:
			res_str += item + ','
			res_str += ','.join([str(x) for x in res_table[item]])
			res_str += '\n'
		return res_str

#project = read_data.Data(data_sets['s_demo']['data'], data_sets['s_demo']['chroms'])

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('static', filename='main_new.html'))

@app.route('/static/<page>')
def send_page(page):
	with open('./static/{}'.format(page), 'rb') as f:
		res = f.read()
	return res

# return all available projects
@app.route('/data/loading')
def loading():
	return ','.join(list(data_sets.keys()))

# return all chromosomes and samples of a project
@app.route('/data/<project>')
def send_project_chroms(project):
	if project not in data.keys():
		file_type = data_sets[project]['type']
		if file_type == 'bigWig':
			data[project] = read_data.BigWig(data_sets[project]['data'])
		elif file_type == 'bigBed':
			data[project] = read_data.BigBed(data_sets[project]['data'])
		elif file_type == 'tabix':
			data[project] = read_data.Tabix(data_sets[project]['data'], data_sets[project]['chroms'])
		else:
			raise TypeError("Unsupported File Type")
	
	res = project + '\n'
	for chrom in data[project].chroms:
		res += '{},{}\n'.format(chrom, data[project].chroms[chrom])
	print('res: ' + res)

	return res

@app.route('/data/<project>/<chrom>')
def send_chrom_references(project, chrom):
	available_references = data[project].samples
	res = '\n'.join(available_references)
	return res

@app.route('/data/<project>/<chrom>/<ref>')
def send_available_samples(project, chrom, ref):
	current_project = data[project]

	if "," in ref: # multi ref mode
		refs = ref.strip().split(",")
		ref0 = refs[0]
		current_project.switch_ref(ref0)
		samples = list(current_project.available_samples)
		for ref in refs[1:]:
			samples.remove(ref)
		return '\n'.join(samples)

	else: # single ref mode
		print("switch reference from {} to {}".format(current_project.ref, ref))
		current_project.switch_ref(ref)

		return '\n'.join(list(current_project.available_samples))

@app.route('/data/<project>/<chrom>/<ref>/<mode>/<query>')
def send_data(project, chrom, ref, mode, query):
	print(project, chrom, ref, query)

	query = query.strip()
	samples, nBins, start, end = query.split("-")

	samples = samples.strip().split(",")
	nBins = int(nBins)

	if not start:
		start = 1
	else:
		start = int(start)
	if not end:
		end = None
	else:
		end = int(end)

	if mode == "single":
		data[project].switch_ref(ref)
		res = data[project].get(nBins, chrom, samples, start = start, end = end, return_format = "json")
	elif mode == "double":
		refs = ref.strip().split(",")
		data[project].switch_ref(refs[0])
		dist_0 = data[project].get(nBins, chrom, samples, start = start, end = end)
		data[project].switch_ref(refs[1])
		dist_1 = data[project].get(nBins, chrom, samples, start = start, end = end)
		res = []
		blockLength = float(end - start) / nBins
		for idx, sample in enumerate(dist_0):
			res.append({
				"sample": sample,
				"data": []
				})
			for i in range(len(dist_0[sample])):
				if dist_1[sample][i] == 0: # check if denominator == 0
					if dist_0[sample][i] == 0: 
						res[idx]["data"].append(0)
					else: 
						res[idx]["data"].append(blockLength)
				else:
					res[idx]["data"].append(dist_0[sample][i] / dist_1[sample][i])
			res[idx]["data"] = [128 if x > 128 else x for x in res[idx]["data"]]
			res[idx]["data"] = [1/128 if x < 1/128 else x for x in res[idx]["data"]]
	elif mode == "multi":
		refs = ref.strip().split(",")
		res = {}
		for ref in refs:
			data[project].switch_ref(ref)
			dist = data[project].get(nBins, chrom, samples, start = start, end = end)
			for sample in samples:
				if sample not in res:
					res[sample] = {}
				res[sample][ref] = dist[sample]

	print("res:\n{}".format(res))
	return jsonify(res)

	"""
	else:
		refs = ref.strip().split(",")
		res = {}
		for idx, ref in enumerate(refs):
			data[project].switch_ref(ref)
			res[ref] = data[project].get(nBins, chrom, samples, start = start, end = end, return_format = "json")
		return jsonify(res)
	"""

	"""
	if mode == "single":
		res.append({"name": ref, "data": []})
		res[0]["data"] = data[project].get(nBins, chrom, samples, start = start, end = end)
		print("Reference: " + ref)
		print(res[ref])
		return jsonify(res)

	elif mode == "double":
		refs = ref.strip().split(",")
		data[project].switch_ref(refs[0])
		dist_0 = data[project].get(nBins, chrom, samples, start = start, end = end)
		data[project].switch_ref(refs[1])
		dist_1 = data[project].get(nBins, chrom, samples, start = start, end = end)
		res["ratio"] = {}
		blockLength = float(end - start) / nBins
		for sample in dist_0:
			res["ratio"][sample] = []
			for i in range(len(dist_0[sample])):
				if dist_1[sample][i] == 0: # check if denominator == 0
					if dist_0[sample][i] == 0: 
						res["ratio"][sample].append(0)
					else: 
						res["ratio"][sample].append(blockLength)
				else:
					res["ratio"][sample].append(dist_0[sample][i] / dist_1[sample][i])
			res["ratio"][sample] = [128 if x > 128 else x for x in res[sample]]
			res["ratio"][sample] = [1/128 if x < 1/128 else x for x in res[sample]]
		print("Ratio")
		print(res["ratio"])
		return jsonify(res)

	elif mode == "multi": # multi refs mode
		# New Method
		for idx, ref in enumerate(refs):
			data[project].switch_ref(ref)
			res[ref] = data[project].get(nBins, chrom, samples, start = start, end = end)
			print("Reference: " + ref)
			print(res[ref])
		return jsonify(res)
	"""

	""" Old Method
	res = {}
	refs_dict = []
	temp_mat = {} # store smallest distances
	for idx, ref in enumerate(refs):
		refs_dict.append({ref: idx})
		data[project].switch_ref(ref)
		dist_mat = data[project].get(nBins, chrom, samples, start = start, end = end)
		print(dist_mat)
		if not temp_mat: # for the first sample
			temp_mat = dist_mat
			for sample in dist_mat:
				res[sample] = [idx for x in dist_mat[sample]]
			continue
		else:
			for sample in dist_mat:
				for i in range(len(dist_mat[sample])):
					if dist_mat[sample][i] < temp_mat[sample][i]:
						temp_mat[sample][i] = dist_mat[sample][i]
						res[sample][i] = idx
	res = to_csv_format(res)
	print(res)
	return res
	"""

@app.route('/tree/<project>/<chrom>/<accessions>/<start>/<end>')
def send_tree(project, chrom, accessions, start, end):
	print("Making tree\nProject:{} Chrom:{}\nAccessions:{}\nStart:{} End:{}".format(project, chrom, accessions, start, end))
	start = int(start)
	end = int(end)

	accessions.strip()
	accessions = accessions.split(",")

	tree = data[project].get_tree(chrom, start, end, accessions, return_format = "newick")

	print("\nTree:\n{}".format(tree))
	return tree


if __name__ == '__main__':
	app.run(host="0.0.0.0", port = 50000, debug = True, threaded = True)
