import dill as pickle
import os
import sys
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, Dataset
import pydicom.uid
from pydicom.uid import generate_uid, PYDICOM_IMPLEMENTATION_UID, ImplicitVRLittleEndian
import tempfile
import datetime

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
        #~ if not os.path.exists(temppath):
        with open(temppath,'wb') as tempfile:
                pickle.dump(ds,tempfile,protocol=3)
                #pickle.dump(ds,tempfile)
                tempfile.close()
        return

def add_all(dataset1,dataset2):
        groups_to_copy = [int(0x8),int(0x10)]
        for element in dataset2:
                #~ print element.tag.group
                if element.tag.group in groups_to_copy:
                        val = None
                        try:
                                val = dataset1[pydicom.tag.Tag(element.tag)].value
                        except KeyError:
                                dataset1.add_new(element.tag, element.VR, element.value)
                        except:
                                raise
                        if val=="":
                                dataset1.add_new(element.tag, element.VR, element.value)
        return dataset1

def save_dicom(images,directory,
				ref=None,
				series_number='add_thousand' ,
				series_description = "MIPPY saved images",
				series_description_append = None,
				path_append = None,
				fnames = None,
				rescale_slope = 'use_bitdepth',
				rescale_intercept = 'use_bitdepth',
				sop_class = 'use_ref',
				slice_positions = 'use_ref'):
	
	"""
	Takes a list of numpy arrays of pixels, and either generates
	whole new DICOM objects with minimal information or uses
	reference DICOM objects to generate series description etc
	"""
	
	if ref is None:
		print("Please pass reference images - ref image list must be the same length as images to be saved")
		pass
	
	suffix = '.dcm'
	ser_uid = generate_uid()
	
	
	
	if isinstance(images, list):
		# Convert to 3D numpy array for simplicity!
		images = np.array(images)
	
	images_out = []
	for i in range(len(images)):
		tempname = tempfile.NamedTemporaryFile(suffix=suffix).name
		file_meta = Dataset()
		file_meta.MediaStorageSOPClassUID = ref[i].file_meta.MediaStorageSOPClassUID
		file_meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID
		file_meta.MediaStorageSOPInstanceUID = generate_uid()
		file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
				
		ds = FileDataset(tempname,{},file_meta=file_meta,preamble=b"\0"*128)
		ds.is_little_endian = True
		ds.is_implicit_VR = True
		add_all(ds,ref[i])
		ds.SeriesInstanceUID = ser_uid
		ds.SOPInstanceUID = generate_uid()
		ds.StudyInstanceUID = ref[i].StudyInstanceUID
		
		if series_description_append is None:
			ds.SeriesDescription = series_description
		else:
			ds.SeriesDescription = ds.SeriesDescription+series_description_append
		
		ds.SamplesPerPixel = 1
		ds.PhotometricInterpretation = 'MONOCHROME2'
		ds.Rows = np.shape(images)[1]
		ds.Columns = np.shape(images)[2]
		ds.WindowCenter = np.min(images)+(np.max(images)-np.min(images))/2
		ds.WindowWidth = np.max(images)-np.min(images)
		ds.BitsAllocated = 16
		ds.BitsStored = 12
		ds.InstanceNumber = i
		ds.ImagePositionPatient = ref[i].ImagePositionPatient
		ds.ImageOrientationPatient = ref[i].ImageOrientationPatient
		ds.PixelSpacing = ref[i].PixelSpacing
		ds.HighBit = 11
		ds.FrameOfReferenceUID = ref[i].FrameOfReferenceUID
		ds.PixelRepresentation = 0
		
		if rescale_slope=='use_ref':
			ds.RescaleSlope = ref[i].RescaleSlope
		elif rescale_slope=='use_bitdepth':
			ds.RescaleSlope =  np.max(np.abs(images)) / (2**ds.BitsStored-1)
		else:
			ds.RescaleSlope = 1
		
		if rescale_intercept=='use_ref':
			ds.RescaleIntercept = ref[i].RescaleIntercept
		elif rescale_intercept=='use_bitdepth':
			ds.RescaleIntercept = 0.-np.min(np.abs(images))
		else:
			ds.RescaleIntercept = 0
			
		#~ print(np.max(images[i]),ds.RescaleSlope,ds.RescaleIntercept)
		
		if series_number=='same':
			ds.SeriesNumber = ref[i].SeriesNumber
		elif series_number=='add_thousand':
			ds.SeriesNumber = ref[i].SeriesNumber+1000
		else:
			ds.SeriesNumber=0
		if not path_append is None:
			outdir = directory+'_'+str(path_append)
		else:
			outdir = directory
		if not os.path.exists(outdir):
			os.makedirs(outdir)
		ds.PixelData = ((images[i]-ds.RescaleIntercept)/ds.RescaleSlope).astype(np.uint16)
		ds.SmallestImagePixelValue = np.min(np.array(ds.PixelData)).astype(np.uint16)
		ds.LargestImagePixelValue = np.max(np.array(ds.PixelData)).astype(np.uint16)
		ds.save_as(os.path.join(outdir,fnames[i]))
	return
	
	