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
			max = np.max(images)
			min = np.min(images)
			ds.RescaleSlope = (max-min) / (2**ds.BitsStored-1)
		elif not rescale_slope is None:
			try:
				ds.RescaleSlope = float(rescale_slope)
			except:
				ds.RescaleSlope = 1
		else:
			ds.RescaleSlope = 1

		if rescale_intercept=='use_ref':
			ds.RescaleIntercept = ref[i].RescaleIntercept
		elif rescale_intercept=='use_bitdepth':
			ds.RescaleIntercept = 0.+np.min(images)
		elif not rescale_intercept is None:
			try:
				ds.RescaleIntercept = float(rescale_intercept)
			except:
				ds.RescaleIntercept = 0
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


# TO finish!


# def load_4d_data(dcm_paths,temp_data_path = None):
#     """
#     Takes a list of paths to DICOM files, and attempts to open as a 4D dataset
#     with consistent X,Y,Z dimensions.
#
#     Allows you to specify a temp_data file holding a pickled dump of a 4D
#     numpy array.
#     """
#     if not temp_data_path is None:
#         "Loading earlier dump of data"
#         win.Im4Dfull = np.load(win.tempdatafile)
#         win.dynamics = np.shape(win.Im4Dfull)[0]
#         win.slices = np.shape(win.Im4Dfull)[1]
#         win.rows = np.shape(win.Im4Dfull)[2]
#         win.columns = np.shape(win.Im4Dfull)[3]
#         win.shape3d = (win.slices,win.rows,win.columns)
#         win.tfull = np.load(win.temptimefile)
#     else:
#         win.Im4Dfull = None
#
#     if win.Im4Dfull is None:
#         slice_positions = []
#         s1 = None
#         s2 = None
#         if len(np.unique(np.array(win.images)))==1:
#             # Same path for every image, most likely single multi-frame image
#             imfiles = [win.images[0]]
#             output(win,"{} image file received...".format(len(imfiles)))
#         else:
#             imfiles = win.images
#             output(win,"{} images received...".format(len(imfiles)))
#         px_list = list(range(len(imfiles)))
#         output(win,"Reading the image data; this may take some time")
#         time.sleep(2)
#         time.sleep(2)
#         i=0
#         win.repetition_time = 0.
#         win.mosaic = False
#         rows = 0
#         columns = 0
#         win.n_in_mosaic = 0
#         win.n_in_mosaic_sq = 0
#         sq = 0
#         classic_dicom = False
#         enhanced = False
#         win.missing_data = False
#         for im in imfiles:
#             i+=1
#             if i%100==0:
#                 output(win,"Reading {}/{}".format(i,len(imfiles)))
#                 gc.collect()
#             #~ output(win,'... opening DICOM')
#             ds = pydicom.dcmread(im,force=True)
#             #~ output(win,'... finished opening DICOM')
#
#             instance = ds.InstanceNumber
#             win.series_number = ds.SeriesNumber
#             try:
#                 win.series_description = ds.SeriesDescription
#             except AttibuteError:
#                 win.series_description = "UNKNOWN SERIES DESCRIPTION"
#
#             if i==1:
#
#                 if 'MOSAIC' in ds.ImageType:                        # Find out how to reshape pixel data if mosaic
#                     win.mosaic = True
#                     rows = ds.Rows
#                     columns = ds.Columns
#                     win.n_in_mosaic = ds[0x19,0x100a].value
#                     found_square = False
#                     while not found_square:
#                         sq+=1
#                         if sq**2>win.n_in_mosaic:
#                             found_square = True
#                     win.n_in_mosaic_sq = sq**2
#                     px_list = list(range(len(imfiles)*win.n_in_mosaic_sq))
#
#                     win.repetition_time = float(ds.RepetitionTime)
#                     win.echo_time = float(ds.EchoTime)
#                     win.PixelSpacing = ds.PixelSpacing
#                     win.slice_thickness = ds.SliceThickness
#                     #~ print(len(px_list))
#                 elif 'ENHANCED' in ds.SOPClassUID.name.upper():
#                     enhanced = True
#                     # Multi-frame image.  Use n_frames as number of images
#                     px_list = list(range(ds.NumberOfFrames))
#                     s1 = ds[0x5200,0x9230][0][0x20,0x9113][0].ImagePositionPatient
#                     s2 = ds[0x5200,0x9230][1][0x20,0x9113][0].ImagePositionPatient
#                     win.repetition_time = float(ds[0x5200,0x9229][0][0x18,0x9112][0].RepetitionTime)
#                     win.echo_time = float(ds[0x5200,0x9230][0][0x18,0x9114][0][0x18,0x9082].value)
#                     win.PixelSpacing = ds[0x5200,0x9230][0][0x28,0x9110][0].PixelSpacing
#                     win.slice_thickness = ds[0x5200,0x9230][0][0x28,0x9110][0].SliceThickness
#                 else:
#                     classic_dicom = True
#                     s1 = ds.ImagePositionPatient
#                     win.repetition_time = float(ds.RepetitionTime)
#                     win.echo_time = float(ds.EchoTime)
#                     win.PixelSpacing = ds.PixelSpacing
#                     win.slice_thickness = ds.SliceThickness
#             elif i==2 and classic_dicom:
#                 s2 = ds.ImagePositionPatient
#             if not win.mosaic and not enhanced:
#                 # e.g. Siemens data with a single slice per image
#                 max_instance = 0
#                 win.missing_data = False
#                 try:
#                     px_list[instance-1] = ds.pixel_array.astype(np.float64)     # Need to use instance to place slices in list, as can't guarantee files are read in the correct order
#                 except IndexError:
#                     # Missing data from start of series - attempt to correct by placing in "instance - n_images" and then rolling array afterwards by required amount
#                     px_list[instance-1-len(imfiles)] = ds.pixel_array.astype(np.float64)
#                     if instance>max_instance:
#                         max_instance = instance
#                     win.missing_data = True
#                 pos = ds.ImagePositionPatient
#                 if not pos in slice_positions:
#                     slice_positions.append(pos)
#             elif enhanced:
#                 # Lots of frames per file, but only a single slice per frame
#                 # Potential hole for Enhanced, assuming only a single file loaded
#                 for n in range(ds.NumberOfFrames):
#                     if n%100==0:
#                         output(win,"Reading frame {}/{}".format(n,ds.NumberOfFrames))
#                     px_list[n] = get_px_array(ds,enhanced,n+1)
#                     pos = ds[0x5200,0x9230][n][0x20,0x9113][0].ImagePositionPatient
#                     if not pos in slice_positions:
#                         slice_positions.append(pos)
#             else:
#                 # Mosaic image - all slices in a single image, 1 image per dynamic
#                 px = ds.pixel_array.astype(np.float64)
#                 #~ print range(sq)
#                 for y in range(sq):
#                         for x in range(sq):
#                             #~ print x,y
#                             imrows = rows//sq
#                             imcols = columns//sq
#                             px_list[(instance-1)*sq*sq+y*sq+x]=np.array(px[y*imrows:(y+1)*imrows,x*imcols:(x+1)*imcols])
#                 pos = ds.ImagePositionPatient
#                 if not pos in slice_positions:
#                     slice_positions.append(pos)
#         del(ds)
#         gc.collect()
#         if win.missing_data:
#             output(win,'Missing instances from start of series - rearranging data as necessary')
#             for n in range(max_instance-len(px_list)):
#                 px_list.append(px_list.pop(0))
#         Im3D = np.array(px_list)
#         del(px_list)
#         gc.collect()
#         print('Im3D shape:',np.shape(Im3D))
#
#         if win.mosaic:
#             sort_order = 'dsrc'
#         elif s1==s2:
#             sort_order='sdrc'
#         else:
#             sort_order='dsrc'
#
#         if not win.mosaic:
#             win.frames = np.shape(Im3D)[0]
#             win.rows = np.shape(Im3D)[1]
#             win.columns = np.shape(Im3D)[2]
#             win.slices = len(slice_positions)
#             win.dynamics = int(win.frames/win.slices)   #~ added by ND 09/05/2018 after error when running - something like "dynamics not found..."
#             print(win.dynamics,win.slices,win.rows,win.columns)
#         else:
#             win.frames = np.shape(Im3D)[0]
#             win.slices = int(win.n_in_mosaic_sq)
#             win.dynamics = int(win.frames/win.slices)
#             win.rows = int(rows/np.sqrt(win.n_in_mosaic_sq))
#             win.columns = int(columns/np.sqrt(win.n_in_mosaic_sq))
#             print('MOSAIC DETECTED:',win.dynamics,win.slices,win.rows,win.columns)
#         win.shape3d = (win.slices,win.rows,win.columns)
#
#         if sort_order=='drcs':
#             win.Im4Dfull = Im3D.reshape(win.dynamics,win.rows,win.columns,win.slices).swapaxes(1,2).swapaxes(1,3)
#         elif sort_order=='sdrc':
#             win.Im4Dfull = Im3D.reshape(win.slices,win.dynamics,win.rows,win.columns).swapaxes(0,1)
#         elif sort_order=='dsrc':
#             win.Im4Dfull = Im3D.reshape(win.dynamics,win.slices,win.rows,win.columns)
#         del(Im3D)
#         gc.collect()
#         output(win,'4D array shape: {},{},{},{}'.format(win.dynamics,win.slices,win.rows,win.columns))
#         #~ print dynamics,slices,rows,columns
#         win.tfull = (np.array(range(win.dynamics)).astype(np.float64))*win.repetition_time/1000
#
#         #~ np.savetxt(os.path.join(outdir,"Im4D.txt"),Im4Dfull)
#
#         #~ win.Im4Dfull.dump(win.tempdatafile)
#         #~ win.tfull.dump(win.temptimefile)
#
#     # Load pixel data to canvas
#     # Load average across all timepoints for each slice
#     # Attempting this in a one-liner using list comprehension and an averaging along first axis
#     win.im1.load_images([imslice for imslice in np.mean(win.Im4Dfull,axis=0)])
#     output(win,'Average for all dynamics displayed on canvas')
#
#
#
#     for i in range(win.slices):
#         win.iminfo[0].append(collect_acq_info(win.images[i]))
#     return
