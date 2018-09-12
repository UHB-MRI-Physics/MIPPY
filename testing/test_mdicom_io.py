from mippy.mdicom.io import *
import pydicom
import numpy as np
import os

def test_save_dicom():
	ds = pydicom.dcmread('test_data/ExampleDICOM/001.IMA')
	outdir = 'test_data/DCM-out'
	px_data = ds.pixel_array.astype(np.float64)*1000
	new_shape = (1,np.shape(px_data)[0],np.shape(px_data)[1])
	save_dicom(px_data.reshape(new_shape),outdir,ref=[ds],
				fnames=['saved001.DCM'],rescale_slope='use_bitdepth',
				rescale_intercept='use_bitdepth')
	print(os.listdir(outdir))
	ds_loaded = pydicom.dcmread('test_data/DCM-out/saved001.DCM')
	assert ds_loaded.pixel_array == 1000*ds.pixel_array
	assert ds_loaded.SOPInstanceUID != ds.SOPInstanceUID