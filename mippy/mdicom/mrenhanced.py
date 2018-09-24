import copy
from pydicom.tag import Tag
import pydicom

def get_frame_ds_old(frame,ds):
    # "frame" starts from 1, not 0.  Need to subtract 1 for correct indexing.
    slicenum = frame-1
    n_frames = ds.NumberOfFrames
    print("Extracting frame "+str(frame)+" of "+str(n_frames))
#        print "    Copying original dataset"
    ds_new = copy.deepcopy(ds)
#        ds_new = pickle.loads(pickle.dumps(ds))
#        ds_new = ujson.loads(ujson.dumps(ds))
#        ds_new = Dataset()
#        ds_new = add_all(ds_new,ds)
#        print ds._character_set
#        print "    Stripping out old tags"
    del ds_new[Tag(0x5200,0x9230)]
    del ds_new[Tag(0x5200,0x9229)]
#        print "    Adding new tags"
    ds_new = add_all(ds_new,ds[0x5200,0x9229][0])
    ds_new = add_all(ds_new,ds[0x5200,0x9230][slicenum])
#        print "    Correcting rows and columns"
    rows = int(ds_new.Rows)
    cols = int(ds_new.Columns)
#        print "    Copying pixel data"
    ds_new.PixelData = ds.PixelData[slicenum*(rows*cols*2):(slicenum+1)*(rows*cols*2)]
#        print "    Replacing instance number"
    ds_new.InstanceNumber = frame
    ds_new.NumberOfFrames = 1
    # print(ds_new._character_set)
    # for i in range(len(ds_new._character_set)):
    #         ds_new._character_set[i] = pydicom.charset.default_encoding
    # print(ds_new._character_set)
    # ds_new._character_set = ds._character_set
    # ds_new._character_set = pydicom.charset.default_encoding
    # ds_new = ds_new._replace(_character_set=pydicom.charset.default_encoding)
#        print "    Returning split dataset"
    print(ds_new)
    
    return ds_new
        
def get_frame_ds(frame,ds):
    """
    This new function creates a DICOM dataset from scratch rather than performing
    a deepcopy, (hopefully) providing a speed increase over the old method.
    """
    slicenum=frame-1    # Frame numbers indexed from 1, not 0
    n_frames = ds.NumberOfFrames
    print("Extracting frame {} of {}".format(frame,n_frames))
    
    file_meta = ds.file_meta
    filename = 'temp'
    suffix = '.dcm'
    
    
    ds_new = pydicom.dataset.FileDataset(filename,{},file_meta=file_meta,preamble=b"\0"*128)
    ds_new.file_meta = ds.file_meta
    ds_new.preamble=bytes("\0"*128,'utf-8')
    if 'Explicit' in ds_new.file_meta.TransferSyntaxUID.name:
        ds_new.is_implicit_VR = False
    else:
        ds_new.is_implicit_VR = True
    if 'Little' in ds_new.file_meta.TransferSyntaxUID.name:
        ds_new.is_little_endian = True
    else:
        ds_new.is_little_endian = False
    # ds_new.is_implicit_VR = True
    # ds_new.is_little_endian = True
    # Add all tags from ds to ds_new
    ds_new = add_all_simple(ds_new,ds)
    # Delete "enhanced" tags
    del ds_new[Tag(0x5200,0x9229)]
    del ds_new[Tag(0x5200,0x9230)]
    # Re-add nested tags from enhanced per-frame groups to main DICOM header
    ds_new = add_all(ds_new,ds[0x5200,0x9229][0])
    ds_new = add_all(ds_new,ds[0x5200,0x9230][slicenum])
    # Correct pixel data to be of the correct frame
    rows = int(ds_new.Rows)
    cols = int(ds_new.Columns)
    ds_new.PixelData = ds.PixelData[slicenum*(rows*cols*2):(slicenum+1)*(rows*cols*2)]
    # Reset InstanceNumber and number of frames
    ds_new.InstanceNumber = frame
    ds_new.NumberOfFrames = 1
    # Change SOP Class UID to MR Image Storage
    ds_new.SOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
    # Return new dataset
    ds_str = str(ds_new)
    return ds_new
    
def add_all_simple(dataset1,dataset2):
    for element in dataset2:
        dataset1.add_new(element.tag,element.VR,element.value)
    return dataset1

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
