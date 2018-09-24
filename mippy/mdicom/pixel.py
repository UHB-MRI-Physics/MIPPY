import numpy as np
from PIL import Image
import io
import binascii

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
                except:
                        raise
        except:
                raise
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
                z = slcspc
                trans_arr = np.array([        [        q[0]*x, q[3]*y, q[6]*z, p[0]        ],
                                                        [        q[1]*x, q[4]*y, q[7]*z, p[1]        ],
                                                        [        q[2]*x, q[5]*y, q[8]*z, p[2]        ],
                                                        [        0., 0., 0., 1.                                ]])
        else:
                coord_arr = np.array([coords[0],coords[1],0.,1.])
                trans_arr = np.array([        [        q[0]*x, q[3]*y, 0., p[0]        ],
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
                trans_arr = np.array([        [        q[0]*x, q[3]*y, q[6]*z, p[0]        ],
                                                        [        q[1]*x, q[4]*y, q[7]*z, p[1]        ],
                                                        [        q[2]*x, q[5]*y, q[8]*z, p[2]        ],
                                                        [        0., 0., 0., 1.                                ]])
        else:
                coord_arr = np.array([coords[0],coords[1],0.,1.])
                trans_arr = np.array([        [        q[0]*x, q[3]*y, 0., p[0]        ],
                                                        [        q[1]*x, q[4]*y, 0., p[1]        ],
                                                        [        q[2]*x, q[5]*y, 0., p[2]        ],
                                                        [        0., 0., 0., 1.                        ]])
        
        if np.linalg.det(trans_arr)==0:
                # No rotation required, use simple scaling as cannot calculate inverse
                i = (coords[0]-p[0])/x
                j = (coords[1]-p[1])/y
                if len(coords)>2:
                        k = (coords[2]-p[3])/z
                else:
                        k=0.
                return tuple([i,j,k])
        
        inverse_trans_array = np.linalg.inv(trans_arr)
        result = np.matmul(inverse_trans_array,coord_arr)
        return tuple(result[0:3])

# TEST FUNCTION, ONLY RUNS IF FILE IS CALLED DIRECTLY
if __name__ == '__main__':
        orient = [1,0,0,0,-1,0]
        position = [-3.8,-20.4,120.8]
        xspc = 0.94
        yspc = 0.94
        im_coords = [100,70]
        pt_coords = get_voxel_location(im_coords,position,orient,xspc,yspc)
        print(pt_coords)
        