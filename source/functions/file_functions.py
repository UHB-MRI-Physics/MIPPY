import os
import csv
from datetime import datetime
import numpy as np
import tkMessageBox

def list_all_files(directory,file_list=[],recursive=False):
	files_in_dir = os.listdir(directory)
	for f in files_in_dir:
		path = os.path.join(directory,f)
		if os.path.isdir(path):
			if recursive:
				file_list = list_all_files(path,file_list=file_list,recursive=True)
			else:
				continue
		else:
			file_list.append(path)
	return file_list

def save_results(results,name=None,directory=None):
	"""
	Standardised way of saving results in TXT files. Not sure what
	to do with them afterwards yet...
	"""
	timestamp = str(datetime.now()).replace(" ","_").replace(":","")
	
	if not name:
		fname = "RESULTS_"+timestamp+".txt"
	else:
		fname = "RESULTS_"+timestamp+"_"+name+".txt"
	
	if not directory:
		current_dir = os.getcwd()
		outputdir = os.path.join(current_dir,"Results")
		if not os.path.exists(outputdir):
			os.makedirs(outputdir)
	else:
		outputdir = directory
		if not os.path.exists(outputdir):
			os.makedirs(outputdir)
	outpath = os.path.join(outputdir,fname)
	with open(outpath,'w') as txtfile:
		txtfile.write(results)
	return