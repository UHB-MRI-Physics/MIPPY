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
			px_bytes = ds.PixelData[(instance-1)*(rows*cols*2):(instance)*(rows*cols*2)]
			px_float = px_bytes_to_array(px_bytes,rows,cols,rs=rs,ri=ri,ss=ss)
		else:
			px_float = generate_px_float(ds.pixel_array.astype(np.float64),rs,ri,ss)
	except:
		return None
	return px_float