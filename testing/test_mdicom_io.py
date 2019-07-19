import sys
import os
sys.path.append(os.getcwd())
import mippy
from mippy.mdicom.io import *
import pydicom
import numpy as np
from shutil import rmtree

def test_save_dicom():
	ds = pydicom.dcmread('test_data/ExampleDICOM/001.IMA')
	outdir = 'test_data/DCM-out'
	if 'RescaleSlope' in dir(ds):
		rs = ds.RescaleSlope
	else:
		rs = 1
	if 'RescaleIntercept' in dir(ds):
		ri = ds.RescaleIntercept
	else:
		ri = 0
	px_data = (ds.pixel_array.astype(np.float64)*rs+ri)*1000
	new_shape = (1,np.shape(px_data)[0],np.shape(px_data)[1])
	save_dicom(px_data.reshape(new_shape),outdir,ref=[ds],
				fnames=['saved001.DCM'],rescale_slope='use_bitdepth',
				rescale_intercept='use_bitdepth')
	#~ print(os.listdir(outdir))
	ds_loaded = pydicom.dcmread('test_data/DCM-out/saved001.DCM')
	px = ds_loaded.pixel_array*ds_loaded.RescaleSlope + ds_loaded.RescaleIntercept
	print(np.max(px),np.max(px_data))
	print(np.sum(px),np.sum(px_data))
	assert np.sum(px)*0.001 >= abs(np.sum(px_data)-np.sum(px))
	assert ds_loaded.SOPInstanceUID != ds.SOPInstanceUID
	rmtree(outdir)

if __name__=='__main__':
	test_save_dicom()