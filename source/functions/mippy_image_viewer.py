from PIL import Image,ImageTk
import dicom
import numpy as np

class DICOMImage(dicom.Dataset):
	"""
	Creates a "viewable" DICOM image by adding an Image and
	PhotoImage instance to a DICOM dataset
	
	All additional attributes have an underscore at the beginning to
	distinguish them from pydicom's attributes
	"""
	
	def __init__(path):
		ds = dicom.read_file(path)
		ds._bitdepth = int(ds.BitsStored)
		pixels = ds.pixel_array.astype(np.float64)
		# DO NOT KNOW IF PIXEL ARRAY ALREADY HANDLES RS AND RI
		try:
			rs = ds[0x28,0x1053].value
		except:
			rs = 1
		try:
			ri = ds[0x28,0x1052].value
		except:
			ri = 0
		try:
			ss = ds[0x2005,0x100E].value
		except:
			ss = 1
		ds._floatpixels = _generate_fp_pixels(pixels, rs, ri, ss)
		ds._8bitpixels = (pixels/np.power(2,ds._bitdepth-8).astype(np.uint8)
		ds._view_pixels = ds._wl_control()
		ds._image = Image.fromarray(ds._8bitpixels)
		ds._viewimage = PhotoImage(ds._image, mode='L')
		return ds
		
	def _generate_fp_pixels(pixels,rs,ri,ss):
		return (pixels*rs+ri)/(rs*ss)

	def _wl_control(self,window=np.power(2,8),level=np.power(2,8)/2):
		self._window = window
		self._level = level
		return np.clip(self._8bitpixels-(level-window/2)*(window/np.power(2,8)),0,255)
