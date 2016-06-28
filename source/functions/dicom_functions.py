import os
import dicom
from dicom.tag import Tag
from dicom.dataset import Dataset
import copy
import numpy as np
from viewer_functions import *
import gc

def get_px_array(ds,enhanced=False,instance=None):
	try:
		rs = float(ds[0x28,0x1053].value)
	except:
		rs = 1.
	try:
		ri = float(ds[0x28,0x1052].value)
	except:
		ri = 0.
	try:
		ss = float(ds[0x2005,0x100E].value)
	except:
		ss = None
	try:
		if enhanced:
			if not instance:
				print "PREVIEW ERROR: Instance/frame number not specified"
				return None
			rows = int(ds.Rows)
			cols = int(ds.Columns)
			print "Bits stored",ds.BitsStored
			print "Rows",rows
			print "Cols",cols
			px_bytes = ds.PixelData[(instance-1)*(rows*cols*2):(instance)*(rows*cols*2)]
			print "Len extracted bytes",len(px_bytes)
			print "Len total px data",len(ds.PixelData)
			px_float = px_bytes_to_array(px_bytes,rows,cols,rs=rs,ri=ri,ss=ss)
		else:
			px_float = generate_px_float(ds.pixel_array.astype(np.float64),rs,ri,ss)
	except:
		return None
	return px_float




def get_frame_ds(ds,frame):
	# "frame" starts from 1, not 0.  Need to subtract 1 for correct indexing.
	slicenum = frame-1
	print "    Copying original dataset"
	ds_new = copy.deepcopy(ds)
#	ds_new = pickle.loads(pickle.dumps(ds))
#	ds_new = ujson.loads(ujson.dumps(ds))
#	ds_new = Dataset()
#	ds_new = add_all(ds_new,ds)
	print "    Stripping out old tags"
	del ds_new[Tag(0x5200,0x9230)]
	del ds_new[Tag(0x5200,0x9229)]
	print "    Adding new tags"
	ds_new = add_all(ds_new,ds[0x5200,0x9229][0])
	ds_new = add_all(ds_new,ds[0x5200,0x9230][slicenum])
	print "    Correcting rows and columns"
	rows = int(ds_new.Rows)
	cols = int(ds_new.Columns)
	print "    Copying pixel data"
	ds_new.PixelData = ds.PixelData[slicenum*(rows*cols*2):(slicenum+1)*(rows*cols*2)]
	print "    Replacing instance number"
	ds_new.InstanceNumber = frame
	ds_new.NumberOfFrames = 1
	print "    Returning split dataset"
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

#def tag_sorter(dictitem):
#	return dictitem[0:-2:1]
	
def collect_dicomdir_info(path,force_read=False):
	tags= None
	# This automatically excludes Philips "XX_" files, but only based on name.  If they've been renamed they
	# won't be picked up until the "try/except" below.
	if os.path.split(path)[1].startswith("XX_"):
		return tags
#	print os.path.split(path)[1]
	
	# Remove any previous datasets just held as "ds" in memory
	ds = None
	#Read file, if not DICOM then ignore
	try:
		ds = dicom.read_file(path, force=force_read)				
		gc.collect()
	except Exception:
		print path+'\n...is not a valid DICOM file and is being ignored.'
		return tags
	if ds:
		try:
			# There has to be a better way of testing this...?
			# If "ImageType" tag doesn't exist, then it's probably an annoying "XX" type file from Philips
			type = ds.ImageType
		except Exception:
			return tags
		try:
			# Some manufacturers use a handy "series description" tag, some don't
			seriesdesc = ds.SeriesDescription
		except Exception:
			try:
				# Some store "protocol name", which will do for now until I find something better
				seriesdesc = ds.ProtocolName
			except Exception:
				# If all else fails, just use a generic string
				seriesdesc = "Unknown Study Type"
		
		if "PHOENIXZIPREPORT" in seriesdesc.upper():
			# Ignore any phoenix zip report files from Siemens
			return tags
		# Unless told otherwise, assume normal MR image storage
		mode = "Assumed MR Image Storage"
		try:
			mode = str(ds.SOPClassUID)
		except Exception:
			pass
		if "SOFTCOPY" in mode.upper() or "BASIC TEXT" in mode.upper():
			# Can't remember why I have these, I think they're possible GE type files???
			return tags
		if mode.upper()=="ENHANCED MR IMAGE STORAGE":
			# If enhanced file, record number of frames.  This is important for pulling the right imaging
			# data out for the DICOM tree and image previews
			enhanced = True
			frames = ds.NumberOfFrames
		else:
			enhanced = False
			frames = 1
		study_uid = ds.StudyInstanceUID
		series_uid = ds.SeriesInstanceUID
		name = ds.PatientName
		date = ds.StudyDate
		series = ds.SeriesNumber
		time = ds.StudyTime
		try:
			# Some manufacturers use a handy "study description" tag, some don't
			studydesc = ds.StudyDescription
		except Exception:
			try:
				# Philips stores "body part examined", which will do for now until I find something better
				studydesc = ds.BodyPartExamined
			except Exception:
				# If all else fails, just use a generic string
				studydesc = "Unknown Study Type"
		
		if not tags:
			tags = []
		
		if enhanced:
			# Set "instance" array to match number of frames
			instance = np.array(range(frames))+1
		else:
			# Of if not enhanced/multi-frame, just create a single element list so that the code
			# below still works
			instance = [ds.InstanceNumber]
		
		for i in instance:
			if not enhanced:
				instance_uid = ds.SOPInstanceUID
			else:
				# Append instance UID with the frame number to give unique reference to each slice
				instance_uid = ds.SOPInstanceUID+"_"+str(i).zfill(3)
			
			pxfloat=get_px_array(ds,enhanced,i)
			if pxfloat is None:
				continue
			
			# Append the information to the "tag list" object
			tags.append(dict([('date',date),('time',time),('name',name),('studyuid',study_uid),
					('series',series),('seriesuid',series_uid),('studydesc',studydesc),
					('seriesdesc',seriesdesc),('instance',i),('instanceuid',instance_uid),
					('path',path),('enhanced',enhanced),('px_array',pxfloat)]))
	return tags