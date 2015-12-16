import os

def list_all_files(dir,file_list=[],recursive=False):
	files_in_dir = os.listdir(dir)
	for f in files_in_dir:
		path = os.path.join(dir,f)
		if os.path.isdir(path):
			if recursive:
				file_list = list_all_files(path,file_list=file_list,recursive=True)
			else:
				continue
		else:
			file_list.append(path)
	return file_list