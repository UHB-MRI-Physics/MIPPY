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
	
	Results are expected in the format of a dictionary, e.g.
		results = {
			'SNR Tra': snr_tra,
			'SNR Sag': snr_sag,
			'SNR Cor': snr_cor,
			'SNR Mean': snr_mean,
			'SNR Std': snr_std,
			'SNR CoV': snr_cov}
	
	Values can be lists, e.g. multiple ROIs or profiles. However, all lists
	must be of the same length.
	"""
	timestamp = str(datetime.now()).replace(" ","_").replace(":","")
	
	if not name:
		fname = "RESULTS_"+timestamp+".csv"
	else:
		fname = "RESULTS_"+timestamp+"_"+name+".csv"
	
	result_header = []
	result_values = []
	for key,value in results.items():
		result_header.append(key)
		result_values.append(value)
	result_array = np.array(result_values,dtype=np.float64)
	result_array = np.transpose(result_array)
	try:
		lines = np.shape(result_array)[1]
	except IndexError:
		result_array = np.reshape(result_array,(1,np.shape(result_array)[0]))
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
	with open(outpath,'wb') as csvfile:
		csvwriter = csv.writer(csvfile,delimiter=',')
		csvwriter.writerow(result_header)
		for row in result_array:
			csvwriter.writerow(row)
	
	tkMessageBox.showinfo("INFO","Results saved to:\n"+outpath)
	
	return