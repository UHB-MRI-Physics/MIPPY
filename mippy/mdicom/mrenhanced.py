import copy
from dicom.tag import Tag

def get_frame_ds(frame,ds):
	# "frame" starts from 1, not 0.  Need to subtract 1 for correct indexing.
	slicenum = frame-1
	n_frames = ds.NumberOfFrames
	print "Extracting frame "+str(frame)+" of "+str(n_frames)
#	print "    Copying original dataset"
	ds_new = copy.deepcopy(ds)
#	ds_new = pickle.loads(pickle.dumps(ds))
#	ds_new = ujson.loads(ujson.dumps(ds))
#	ds_new = Dataset()
#	ds_new = add_all(ds_new,ds)
#	print ds._character_set
#	print "    Stripping out old tags"
	del ds_new[Tag(0x5200,0x9230)]
	del ds_new[Tag(0x5200,0x9229)]
#	print "    Adding new tags"
	ds_new = add_all(ds_new,ds[0x5200,0x9229][0])
	ds_new = add_all(ds_new,ds[0x5200,0x9230][slicenum])
#	print "    Correcting rows and columns"
	rows = int(ds_new.Rows)
	cols = int(ds_new.Columns)
#	print "    Copying pixel data"
	ds_new.PixelData = ds.PixelData[slicenum*(rows*cols*2):(slicenum+1)*(rows*cols*2)]
#	print "    Replacing instance number"
	ds_new.InstanceNumber = frame
	ds_new.NumberOfFrames = 1
	ds_new._character_set = ds._character_set
#	print "    Returning split dataset"
	
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