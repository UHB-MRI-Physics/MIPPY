import os
import dicom
from dicom.tag import Tag
from dicom.dataset import Dataset
import copy
import numpy as np
from viewer_functions import *
import gc
import cPickle as pickle
import sys
from subprocess import call

def compare_dicom(ds1,ds2,diffs=None,num=None,name=''):
	if diffs is None:
		diffs = []
		gc.collect()
	if num:
		num=' ('+str(num).zfill(4)+')'
	else:
		num=''
	exclude_list = ['UID',
				'REFERENCE',	# Don't care what localisers were used
				'SERIES TIME',
				'ACQUISITION TIME',
				'CONTENT TIME',
				'CREATION TIME',
				'PIXEL VALUE',
				'WINDOW',
				'CSA',		# Still don't really know what CSA is
				'PIXEL DATA',
				'PADDING']
	for element in ds1:
		if any(s in element.name.upper() for s in exclude_list):
			continue
		val1 = element.value
		try:
			val2 = ds2[element.tag].value
		except:
			diffs.append((name+str(element.name)+num,str(val1),'--MISSING--'))
			continue
		if element.VR=="SQ":
			for i in range(len(val1)):
				compare_dicom(val1[i],val2[i],diffs=diffs,num=i,name=str(element.name)+' >> ')
			continue
		if not val1==val2:
			if not any(s in element.name.upper() for s in exclude_list):
				diffs.append((name+str(element.name)+num,str(val1),str(val2)))
	for element in ds2:
		val2 = element.value
		try:
			val1 = ds1[element.tag].value
		except:
			diffs.append((name+str(element.name)+num,'--MISSING--',str(val2)))
			continue
	
	return diffs

def get_px_array(ds,enhanced=False,instance=None):
	if 'JPEG' in str(ds.file_meta[0x2,0x10].value):
		compressed = True
	else:
		compressed = False
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
#			print "Bits stored",ds.BitsStored
#			print "Rows",rows
#			print "Cols",cols
			px_bytes = ds.PixelData[(instance-1)*(rows*cols*2):(instance)*(rows*cols*2)]
#			print "Len extracted bytes",len(px_bytes)
#			print "Len total px data",len(ds.PixelData)
			px_float = px_bytes_to_array(px_bytes,rows,cols,rs=rs,ri=ri,ss=ss)
		else:
			px_float = generate_px_float(ds.pixel_array.astype(np.float64),rs,ri,ss)
	except:
		return None
	return px_float




def get_frame_ds(ds,frame):
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

#def tag_sorter(dictitem):
#	return dictitem[0:-2:1]
	
def collect_dicomdir_info(path,tempdir=None,force_read=False):
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
		# Ignore "OT" (other?) modality DICOM objects - for now at least...
		modality = ds.Modality
		if (
			'OT' in modality
			):
			return tags
		
		transfer_syntax =  str(ds.file_meta[0x2,0x10].value)
		if 'JPEG' in transfer_syntax:
			compressed = True
		else:
			compressed = False

			
			
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
			# Or if not enhanced/multi-frame, just create a single element list so that the code
			# below still works
			try:
				instance = [ds.InstanceNumber]
			except AttributeError:
				print "INSTANCE NUMBER TAG DOESN'T EXIST"
				print path
				raise
		
		instance_uid = 'UNKNOWN'
		
		for i in instance:
			if not enhanced:
				instance_uid = ds.SOPInstanceUID
			else:
				# Append instance UID with the frame number to give unique reference to each slice
				instance_uid = ds.SOPInstanceUID+"_"+str(i).zfill(3)
		
			if compressed:
				# Check if temp file already exists for that InstanceUID. If so, read that file. If not, 
				# uncompress the file and replace ds. Dataset will get saved as temp file at the end of this
				# function.
				temppath = os.path.join(tempdir,instance_uid+'.mds')
				if os.path.exists(temppath):
					print seriesdesc+' '+str(i).zfill(3)
					print "    COMPRESSED DICOM - Temp file found"
					with open(temppath,'rb') as tempfile:
						ds = pickle.load(tempfile)
					tempfile.close()
				else:
					# Uncompress the file
					outpath=os.path.join(tempdir,'UNCOMP_'+instance_uid+'.DCM')
					print seriesdesc+' '+str(i).zfill(3)
					print "    COMPRESSED DICOM - Uncompressing"
					if 'darwin' in sys.platform:
						#dcmdjpeg=os.path.join(os.getcwd(),'lib','dcmdjpeg_mac')
						dcmdjpeg=r'./lib/dcmdjpeg_mac'
					elif 'linux' in sys.platform:
						dcmdjpeg=r'./lib/dcmdjpeg_linux'
					elif 'win' in sys.platform:
						dcmdjpeg=r'lib\dcmdjpeg_win.exe'
					else:
						print "UNSUPPORTED OPERATING SYSTEM"
						print str(sys.platform)
					command = dcmdjpeg+' \"'+path+'\" \"'+outpath+'\"'
					call(command, shell=True)
					#~ path = outpath
					ds = dicom.read_file(outpath)
				
			
			pxfloat=get_px_array(ds,enhanced,i)
			if pxfloat is None:
				continue
			
			# Append the information to the "tag list" object
			tags.append(dict([('date',date),('time',time),('name',name),('studyuid',study_uid),
					('series',series),('seriesuid',series_uid),('studydesc',studydesc),
					('seriesdesc',seriesdesc),('instance',i),('instanceuid',instance_uid),
					('path',path),('enhanced',enhanced),('compressed',compressed),
					('px_array',pxfloat)]))
		# Assuming all this has worked, serialise the dataset (ds) for later use, with the instance UID
		# as the file number
		if not enhanced:
			if tempdir:
				save_temp_ds(ds,tempdir,instance_uid+'.mds')
		
	return tags
	
def save_temp_ds(ds,tempdir,fname):
	'''
	I don't know why this bit needs to be done, but if you don't create these strings
	for each slice, python isn't able to pickle the objects properly and complains
	about not having the Attribute _character_set - perhaps the character set isn't
	defined until a string representation of the object is required?
	'''
	ds_str = str(ds)
	if not os.path.exists(tempdir):
		os.makedirs(tempdir)
	temppath = os.path.join(tempdir,fname)
	if not os.path.exists(temppath):
		with open(temppath,'wb') as tempfile:
			pickle.dump(ds,tempfile,protocol=2)
			tempfile.close()
	return
