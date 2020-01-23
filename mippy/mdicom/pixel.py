import numpy as np
from PIL import Image
import io
import binascii
from pydicom.filebase import DicomBytesIO
from pydicom import dcmread
import gc

def get_px_array(ds,enhanced=False,instance=None,bitdepth=None):
        if 'JPEG' in str(ds.file_meta[0x2,0x10].value):
                compressed = True
                print("DATA IS JPEG COMPRESSED - UNABLE TO PRODUCE PIXEL ARRAY")
                #~ print "Data is JPEG compressed. Uncompressing within MIPPY"
                return None
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
        except KeyError:
                try:
                        # Scaling buried per-frame in functional groups sequence
                        ss = float(ds[0x5200,0x9230][instance-1][0x2005,0x140f][0][0x2005,0x100E].value)
                except KeyError:
                        ss = None
                except TypeError:
                        # Problem with some DICOM encoders (namely PukkaJ) that don't write the 2005,140f tag
                        # properly.  This is currently unrecoverable, so just assume ss doesn't exist.
                        ss = None
                except:
                        raise
        except:
                raise

        ss = None   # Added in v2.8, attempting to remove problem with quantitative imaging
                    # on Philips scanners - overrules any additional scaling factor stored
                    # in the "real world value mapping" tag on Philips MRI and only uses
                    # the standard rescale slope and intercept


        #~ print("Scaling: RS {},RI {},SS {}".format(rs,ri,ss))
        if ds.is_little_endian:
                mode = 'littleendian'
        else:
                mode = 'bigendian'
        #~ print(enhanced,mode)
        if compressed:
                # Grab raw pixel array
                #~ pixel_data_unpacked = binascii.unhexlify(ds.PixelData)
                pixel_data_unpacked = ds.PixelData
        try:
                if not compressed:
                        if enhanced:
                                if not instance:
                                        print("PREVIEW ERROR: Instance/frame number not specified")
                                        return None
                                rows = int(ds.Rows)
                                cols = int(ds.Columns)
                                px_bytes = ds.PixelData[(instance-1)*(rows*cols*2):(instance)*(rows*cols*2)]
                                px_float = px_bytes_to_array(px_bytes,rows,cols,rs=rs,ri=ri,ss=ss,mode=mode)
                        else:
                                px_float = generate_px_float(ds.pixel_array.astype(np.float64),rs,ri,ss)
                #~ else:
                        #~ if enhanced:
                                #~ if not instance:
                                        #~ print "PREVIEW ERROR: Instance/frame number not specified"
                                        #~ return None
                                #~ rows = int(ds.Rows)
                                #~ cols = int(ds.Columns)
                                #~ px_bytes = pixel_data_unpacked[0][(instance-1)*(rows*cols*2):(instance)*(rows*cols*2)]
                                #~ px_stream = StringIO.StringIO(px_bytes)
                                #~ px_float = generate_px_float(np.array(Image.open(px_stream)).astype(np.float64),rs=rs,ri=ri,ss=ss)
                        #~ else:
                                #~ rows = int(ds.Rows)
                                #~ cols = int(ds.Columns)
                                #~ px_stream = StringIO.StringIO(pixel_data_unpacked)
                                #~ px_float = generate_px_float(np.array(Image.open(px_stream)).astype(np.float64),rs=rs,ri=ri,ss=ss)
        except:
                raise
                #~ return None
        if not bitdepth is None:
                # Rescale float to unsigned integer bitdepth specified
                # Useful for preview purposes to save memory!!!
                if not (bitdepth==8 or bitdepth==16 or bitdepth==32):
                        print("Unsupported bitdepth - please use 8, 16, 32 (arrays are 64-bit by default)")
                        return None
                min = np.min(px_float)
                max = np.max(px_float)
                range = max-min
                px_float = ((px_float-min)/range)*float((2**bitdepth)-1)
                if bitdepth==8:
                        px_float = px_float.astype(np.uint8)
                elif bitdepth==16:
                        px_float = px_float.astype(np.uint16)
                elif bitdepth==32:
                        px_float = px_float.astype(np.float32)



        return px_float

def px_bytes_to_array(byte_array,rows,cols,bitdepth=16,mode='littleendian',rs=1,ri=0,ss=None):

        if bitdepth==16:
                if mode=='littleendian':
                        this_dtype = np.dtype('<u2')
                elif mode=='bigendian':
                        this_dtype = np.dtype('>u2')
                else:
                        print("Unsupported mode - use either littleendian or bigendian")
                        return None
        elif bitdepth==8:
                this_dtype = np.dytpe('u1')
        abytes = np.frombuffer(byte_array, dtype=this_dtype)
#        print np.mean(abytes)
#        print np.shape(abytes)
#        print abytes
        abytes = abytes.reshape((cols,rows)).astype(np.float64)
        px_float = generate_px_float(abytes,rs,ri,ss)
#        print np.mean(px_float)
        return px_float

def generate_px_float(pixels,rs,ri,ss=None):
        if not ss is None:
                return (pixels*rs+ri)/(rs*ss)
        else:
                return (pixels*rs+ri)

def get_voxel_location(coords,slice_location,slice_orientation,pxspc_x,pxspc_y,slcspc=None):
        # All inputs are tuples/lists of length 3 except spacings
        p = slice_location
        q = slice_orientation
        x = pxspc_x
        y = pxspc_y
        if len(coords)>2:
                coord_arr = np.array([coords[0],coords[1],coords[2],1.])
                #~ q2 = np.cross(q[0:3],q[3:6])
                if len(q)==6:
                        q2 = np.cross(q[0:3],q[3:6])
                        q = np.concatenate((q,q2))
                z = slcspc
                trans_arr = np.array([                  [        q[0]*x, q[3]*y, q[6]*z, p[0]        ],
                                                        [        q[1]*x, q[4]*y, q[7]*z, p[1]        ],
                                                        [        q[2]*x, q[5]*y, q[8]*z, p[2]        ],
                                                        [        0., 0., 0., 1.                                ]])
        else:
                coord_arr = np.array([coords[0],coords[1],0.,1.])
                trans_arr = np.array([                  [        q[0]*x, q[3]*y, 0., p[0]        ],
                                                        [        q[1]*x, q[4]*y, 0., p[1]        ],
                                                        [        q[2]*x, q[5]*y, 0., p[2]        ],
                                                        [        0., 0., 0., 1.                        ]])
        result = np.matmul(trans_arr,coord_arr)
        return tuple(result[0:3])

def get_img_coords(coords,slice_location,slice_orientation,pxspc_x,pxspc_y,slcspc=None):
        # Performs the inverse of get_voxel_location, returning the x,y,z coordinates in the image space
        # of a point (x,y,z) in patient space
        p = slice_location
        q = slice_orientation
        x = pxspc_x
        y = pxspc_y
        if len(coords)>2:
                coord_arr = np.array([coords[0],coords[1],coords[2],1.])
                if len(q)==6:
                        q2 = np.cross(q[0:3],q[3:6])
                        q = np.concatenate((q,q2))
                z = slcspc
                trans_arr = np.array([                  [        q[0]*x, q[3]*y, q[6]*z, p[0]        ],
                                                        [        q[1]*x, q[4]*y, q[7]*z, p[1]        ],
                                                        [        q[2]*x, q[5]*y, q[8]*z, p[2]        ],
                                                        [        0., 0., 0., 1.                                ]])
        else:
                coord_arr = np.array([coords[0],coords[1],0.,1.])
                trans_arr = np.array([                  [        q[0]*x, q[3]*y, 0., p[0]        ],
                                                        [        q[1]*x, q[4]*y, 0., p[1]        ],
                                                        [        q[2]*x, q[5]*y, 0., p[2]        ],
                                                        [        0., 0., 0., 1.                        ]])

        if np.linalg.det(trans_arr)==0:
                # No rotation required, use simple scaling as cannot calculate inverse
                i = (coords[0]-p[0])/x
                j = (coords[1]-p[1])/y
                if len(coords)>2:
                        k = (coords[2]-p[2])/z
                else:
                        k=0.
                return tuple([i,j,k])

        inverse_trans_array = np.linalg.inv(trans_arr)
        result = np.matmul(inverse_trans_array,coord_arr)
        return tuple(result[0:3])

def generate_4d_array(dicom_paths):
    """
    Only works with paths to DICOM files, not pre-loaded datasets.
    """
    Im4Dfull = None
    slice_positions = []
    orientations = []
    pixel_spacing = None
    s1 = None
    s2 = None
    if len(np.unique(np.array(dicom_paths)))==1:
        # Same path for every image, most likely single multi-frame image
        imfiles = [dicom_paths[0]]
        print("{} image file received...".format(len(imfiles)))
    else:
        imfiles = dicom_paths
        print("{} images received...".format(len(imfiles)))
    px_list = list(range(len(imfiles)))
    print(px_list)
    print("Reading the image data; this may take some time")
    # time.sleep(2)
    # time.sleep(2)
    i=0
    repetition_time = 0.
    mosaic = False
    rows = 0
    columns = 0
    n_in_mosaic = 0
    n_in_mosaic_sq = 0
    sq = 0
    classic_dicom = False
    enhanced = False
    missing_data = False
    for im in imfiles:
        i+=1
        if i%100==0:
            print("Reading {}/{}".format(i,len(imfiles)))
            gc.collect()
        #~ print('... opening DICOM')
        ds = dcmread(im,force=True)
        #~ print('... finished opening DICOM')

        instance = ds.InstanceNumber
        series_number = ds.SeriesNumber
        try:
            series_description = ds.SeriesDescription
        except AttibuteError:
            series_description = "UNKNOWN SERIES DESCRIPTION"

        if i==1:

            if 'MOSAIC' in ds.ImageType:                        # Find out how to reshape pixel data if mosaic
                mosaic = True
                rows = ds.Rows
                columns = ds.Columns
                n_in_mosaic = ds[0x19,0x100a].value
                found_square = False
                while not found_square:
                    sq+=1
                    if sq**2>n_in_mosaic:
                        found_square = True
                n_in_mosaic_sq = sq**2
                px_list = list(range(len(imfiles)*n_in_mosaic_sq))

                repetition_time = float(ds.RepetitionTime)
                echo_time = float(ds.EchoTime)
                PixelSpacing = ds.PixelSpacing
                slice_thickness = ds.SliceThickness
                #~ print(len(px_list))
            elif 'ENHANCED' in ds.SOPClassUID.name.upper():
                enhanced = True
                # Multi-frame image.  Use n_frames as number of images
                px_list = list(range(ds.NumberOfFrames))
                s1 = ds[0x5200,0x9230][0][0x20,0x9113][0].ImagePositionPatient
                s2 = ds[0x5200,0x9230][1][0x20,0x9113][0].ImagePositionPatient
                repetition_time = float(ds[0x5200,0x9229][0][0x18,0x9112][0].RepetitionTime)
                echo_time = float(ds[0x5200,0x9230][0][0x18,0x9114][0][0x18,0x9082].value)
                PixelSpacing = ds[0x5200,0x9230][0][0x28,0x9110][0].PixelSpacing
                slice_thickness = ds[0x5200,0x9230][0][0x28,0x9110][0].SliceThickness
            else:
                classic_dicom = True
                s1 = ds.ImagePositionPatient
                repetition_time = float(ds.RepetitionTime)
                echo_time = float(ds.EchoTime)
                PixelSpacing = ds.PixelSpacing
                slice_thickness = ds.SliceThickness
            pixel_spacing = np.array([float(PixelSpacing[0]),float(PixelSpacing[1])])
        elif i==2 and classic_dicom:
            s2 = ds.ImagePositionPatient
        if not mosaic and not enhanced:
            # e.g. Siemens data with a single slice per image
            max_instance = 0
            missing_data = False
            try:
                px_list[instance-1] = ds.pixel_array.astype(np.float64)     # Need to use instance to place slices in list, as can't guarantee files are read in the correct order
            except IndexError:
                # Missing data from start of series - attempt to correct by placing in "instance - n_images" and then rolling array afterwards by required amount
                px_list[instance-1-len(imfiles)] = ds.pixel_array.astype(np.float64)
                if instance>max_instance:
                    max_instance = instance
                missing_data = True
            pos = ds.ImagePositionPatient
            ori = ds.ImageOrientationPatient
            if not pos in slice_positions:
                slice_positions.append(pos)
            if not ori in orientations:
                orientations.append(ori)
        elif enhanced:
            # Lots of frames per file, but only a single slice per frame
            # Potential hole for Enhanced, assuming only a single file loaded
            for n in range(ds.NumberOfFrames):
                if n%100==0:
                    print("Reading frame {}/{}".format(n,ds.NumberOfFrames))
                px_list[n] = get_px_array(ds,enhanced,n+1)
                pos = ds[0x5200,0x9230][n][0x20,0x9113][0].ImagePositionPatient
                ori = ds[0x5200,0x9230][n][0x20,0x9113][0].ImageOrientationPatient
                if not pos in slice_positions:
                    slice_positions.append(pos)
                if not ori in orientations:
                    orientations.append(ori)
        else:
            # Mosaic image - all slices in a single image, 1 image per dynamic
            px = ds.pixel_array.astype(np.float64)
            #~ print range(sq)
            for y in range(sq):
                    for x in range(sq):
                        #~ print x,y
                        imrows = rows//sq
                        imcols = columns//sq
                        px_list[(instance-1)*sq*sq+y*sq+x]=np.array(px[y*imrows:(y+1)*imrows,x*imcols:(x+1)*imcols])
            pos = ds.ImagePositionPatient
            ori = ds.ImageOrientationPatient
            if not pos in slice_positions:
                slice_positions.append(pos)
            if not ori in orientations:
                orientations.append(ori)
    del(ds)

    # Check orientations - should all be identical
    if len(np.unique(np.array(orientations),axis=0))>1:
        print("Slices not all in the same orientation - abandoning")
        return None

    # Calculate slice spacing
    if len(slice_positions)>1:
        slice_spacing = np.linalg.norm(np.array(slice_positions[1])-np.array(slice_positions[2]))
    else:
        slice_spacing = 1.

    gc.collect()
    if missing_data:
        print('Missing instances from start of series - rearranging data as necessary')
        for n in range(max_instance-len(px_list)):
            px_list.append(px_list.pop(0))
    Im3D = np.array(px_list)
    del(px_list)
    gc.collect()
    print('Im3D shape:',np.shape(Im3D))

    if mosaic:
        sort_order = 'dsrc'
    elif s1==s2:
        sort_order='sdrc'
    else:
        sort_order='dsrc'

    if not mosaic:
        frames = np.shape(Im3D)[0]
        rows = np.shape(Im3D)[1]
        columns = np.shape(Im3D)[2]
        slices = len(slice_positions)
        dynamics = int(frames/slices)   #~ added by ND 09/05/2018 after error when running - something like "dynamics not found..."
        print(dynamics,slices,rows,columns)
    else:
        frames = np.shape(Im3D)[0]
        slices = int(n_in_mosaic_sq)
        dynamics = int(frames/slices)
        rows = int(rows/np.sqrt(n_in_mosaic_sq))
        columns = int(columns/np.sqrt(n_in_mosaic_sq))
        print('MOSAIC DETECTED:',dynamics,slices,rows,columns)
    shape3d = (slices,rows,columns)

    if sort_order=='drcs':
        Im4Dfull = Im3D.reshape(dynamics,rows,columns,slices).swapaxes(1,2).swapaxes(1,3)
    elif sort_order=='sdrc':
        Im4Dfull = Im3D.reshape(slices,dynamics,rows,columns).swapaxes(0,1)
    elif sort_order=='dsrc':
        Im4Dfull = Im3D.reshape(dynamics,slices,rows,columns)
    del(Im3D)
    gc.collect()
    print('4D array shape: {},{},{},{}'.format(dynamics,slices,rows,columns))
    #~ print dynamics,slices,rows,columns
    tfull = (np.array(range(dynamics)).astype(np.float64))*repetition_time/1000

    geometry = {'position':np.array(slice_positions[0]),'orientation':np.array(orientations[0]),
                'spacing':(pixel_spacing[0],pixel_spacing[1],slice_spacing)}

    return Im4Dfull, geometry

def get_coordinate_array(shape,geometry):
    """
    Returns a 3D array the same shape as an image volume containing (x,y,z) coordinate
    tuples representing the 3D location in patient space of each voxel location.

    Parameters
    -------------------
    shape: tuple
        A tuple representing the shape of the array, usually obtained using `numpy.shape()`
    geometry: dict
        A dictionary of the imaging volume geometry, as returned by generate_4d_array. Must contain
        the keys `'position'` (numpy array), `'orientation'` (numpy array) and `'spacing'` (3-tuple of
        x,y,z voxel spacing).


    """

    coords = np.zeros(shape,dtype=(float,3))

    xvec = geometry['spacing'][0]*geometry['orientation'][0:3]
    yvec = geometry['spacing'][1]*geometry['orientation'][3:6]
    zvec = geometry['spacing'][2]*np.cross(geometry['orientation'][0:3],geometry['orientation'][3:6])

    origin = get_voxel_location((0,0,0),geometry['position'],geometry['orientation'],*geometry['spacing'])

    # indices = np.indices(shape)
    # print("indices shape",np.shape(indices))
    # offsets = (zvec*indices[0].flatten() + yvec*indices[1].flatten() + xvec*indices[2].flatten()).reshape(3,shape)
    #
    # coords = coords+origin+offsets
    #
    # print(coords)

    for z in range(shape[0]):
        print("  Slice {} of {}".format(z+1,shape[0]))
        for y in range(shape[1]):
            for x in range(shape[2]):
                coords[z,y,x] = origin + x*xvec + y*yvec + z*zvec


    return coords



# TEST FUNCTION, ONLY RUNS IF FILE IS CALLED DIRECTLY
if __name__ == '__main__':
        orient = [1,0,0,0,-1,0]
        position = [-3.8,-20.4,120.8]
        xspc = 0.94
        yspc = 0.94
        im_coords = [100,70]
        pt_coords = get_voxel_location(im_coords,position,orient,xspc,yspc)
        print(pt_coords)
