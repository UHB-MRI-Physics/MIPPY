import os
import csv

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
	"""
	
	pass