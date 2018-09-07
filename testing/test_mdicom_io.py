from mippy.mdicom.io import *
import pydicom
import numpy as np

def test_save_dicom():
	ds = pydicom.dcmread('test_data/ExampleDICOM/001.IMA')
	px_data = ds.pixel_array.astype(np.float64)*1000
	new_shape = (1,np.shape(px_data)[0],np.shape(px_data)[1])
	save_dicom(px_data.reshape(new_shape),'test_data/DCM-out',ref=[ds],
				fnames=['saved001.DCM'],rescale_slope='use_bitdepth',
				rescale_intercept='use_bitdepth')
	ds_loaded = pydicom.dcmread('test_data/DCM-out/saved001.DCM')
	assert ds_loaded.pixel_array == 1000*ds.pixel_array
	assert ds_loaded.SOPInstanceUID != ds.SOPInstanceUID