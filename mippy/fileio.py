import os
from datetime import datetime

def list_all_files(dirpath,recursive=False):
	pathlist = []
	if recursive:
		for root,directories,files in os.walk(dirpath):
			for filename in files:
				filepath = os.path.join(root,filename)
				pathlist.append(filepath)
	else:
		allobjects = os.listdir(dirpath)
		for f in allobjects:
			thispath = os.path.join(dirpath,f)
			if not os.path.isdir(thispath):
				pathlist.append(thispath)
	return pathlist

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
	
	if directory is None:
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