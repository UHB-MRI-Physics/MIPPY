import os
import dicom
from dicom.tag import Tag
import copy

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
	
def split_enhanced_dicom(ds,frame):
	# "frame" starts from 1, not 0.  Need to subtract 1 for correct indexing.
	slice = frame-1
	ds_new = copy.deepcopy(ds)
	del ds_new[Tag(0x5200,0x9230)]
	del ds_new[Tag(0x5200,0x9229)]
	ds_new = add_all(ds_new,ds[0x5200,0x9229][0])
	ds_new = add_all(ds_new,ds[0x5200,0x9230][slice])
	rows = int(ds_new.Rows)
	cols = int(ds_new.Columns)
	ds_new.PixelData = ds.PixelData[slice*(rows*cols*2):(slice+1)*(rows*cols*2)]
	ds_new.InstanceNumber = frame
	ds_new.NumberOfFrames = 1
	return ds_new

def add_all(dataset1,dataset2):
	for element in dataset2:
		if element.VR=="SQ":
			for D in range(len(element.value)):
				add_all(dataset1,element.value[D])
		else:
			try:
				del dataset1[Tag(element.tag)]
			except KeyError:
				pass
			except:
				raise
			dataset1.add_new(element.tag, element.VR, element.value)
	return dataset1