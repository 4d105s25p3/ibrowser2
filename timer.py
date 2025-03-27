#!/usr/bin/python3

import time

""" The following from https://gist.github.com/turicas/5278558 """
from resource import getrusage as resource_usage, RUSAGE_SELF, RUSAGE_CHILDREN
from time import time as timestamp

def unix_time(function, args=tuple(), kwargs={}):
    '''Return `real`, `sys` and `user` elapsed time, like UNIX's command `time`
    You can calculate the amount of used CPU-time used by your
    function/callable by summing `user` and `sys`. `real` is just like the wall
    clock.
    Note that `sys` and `user`'s resolutions are limited by the resolution of
    the operating system's software clock (check `man 7 time` for more
    details).
    '''
    start_time, start_resources = timestamp(), resource_usage(RUSAGE_SELF)
    function(*args, **kwargs)
    end_resources, end_time = resource_usage(RUSAGE_SELF), timestamp()

    return {'real': end_time - start_time,
            'sys': end_resources.ru_stime - start_resources.ru_stime,
            'user': end_resources.ru_utime - start_resources.ru_utime}
""" Above from https://gist.github.com/turicas/5278558 """

test_records = {'total': [], 'process': [], 'sys': [], 'user': []}
tree_records = {'total': [], 'process': [], 'sys': [], 'user': []}
preprocessing_records = []

records = []

chromosomes_sizes = {}

def run(func, *args, **kwds):

	start_self = resource_usage(RUSAGE_SELF)
	start_child = resource_usage(RUSAGE_CHILDREN)
	start1 = time.perf_counter()
	start2 = time.process_time()

	value = func(*args, **kwds)

	end2 = time.process_time()
	end1 = time.perf_counter()
	end_child = resource_usage(RUSAGE_CHILDREN)
	end_self = resource_usage(RUSAGE_SELF)

	total_time = end1 - start1
	process_time = end2 - start2

	sys_self = end_self.ru_stime - start_self.ru_stime
	user_self = end_self.ru_utime - start_self.ru_utime

	return value, total_time, process_time, sys_self, user_self

def timer(func):
	def wrapper(*args, **kwds):
		function_name = func.__name__

		value, total_time, process_time, sys_self, user_self = run(func, *args, **kwds)
		records.append({
			"function_name": function_name,
			"total_time": total_time,
			"process_time": process_time,
			"system_time": sys_self,
			"user_time": user_self
			})

		return value
	return wrapper

def preprocessing_timer(func):
	def wrapper(*args, **kwds):
		func_name = func.__name__

		value, total_time, process_time, sys_self, user_self = run(func, *args, **kwds)

		preprocessing_records.append([func_name, total_time, process_time, user_self, sys_self])

		return value
	return wrapper

def test_timer(func):
	def wrapper(*args, **kwds):

		value, total_time, process_time, sys_self, user_self = run(func, *args, **kwds)
		
		test_records['total'].append(total_time)
		test_records['process'].append(process_time)

		test_records['sys'].append(sys_self)
		test_records['user'].append(user_self)

		return value
	return wrapper

def tree_timer(func):
	def wrapper(*args, **kwds):

		value, total_time, process_time, sys_self, user_self = run(func, *args, **kwds)
		
		tree_records['total'].append(total_time)
		tree_records['process'].append(process_time)

		tree_records['sys'].append(sys_self)
		tree_records['user'].append(user_self)

		return value
	return wrapper


"""
def another_test_timer(func, *args, **kwds):
	value, total_time, process_time, sys_self, user_self = run(func, *args, **kwds)

	test_records['total'].append(total_time)
	test_records['process'].append(process_time)

	test_records['sys'].append(sys_self)
	test_records['user'].append(user_self)

	return value


def handle_get(args, kwds, total_time, process_time, chrom_sizes):
	nBlock, chrom, samples = args[1:]
	
	full_length = chrom_sizes[chrom]
	nSamples = len(samples)
	
	if 'start' not in kwds.keys():
		kwds['start'] = 1
	if 'end' not in kwds.keys():
		kwds['end'] = full_length
	length = kwds['end'] - kwds['start']
		
	runtime['get'][(nSamples, length)] = {'total_time': total_time, 'process_time': process_time}
"""
