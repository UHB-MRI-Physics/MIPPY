import py_compile
import os
import sys

def compile_all(this_dir):
	file_list = os.listdir(this_dir)
	for f in file_list:
		path = os.path.join(this_dir,f)
		if os.path.isdir(path):
			compile_all(path)
			continue
		if os.path.splitext(f)[1].upper()=='.PY' or os.path.splitext(f)[1].upper()=='.PYW':
			print "COMPILE: ",path
			py_compile.compile(path)
			continue
		else:
			continue

compile_all (sys.argv[1])