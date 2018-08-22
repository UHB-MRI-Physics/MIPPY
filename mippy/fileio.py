import os
from datetime import datetime
from .mdicom.reading import load_images_from_uids

def list_all_files(dirpath,recursive=False):
        pathlist = []
        if recursive:
                for root,directories,files in os.walk(dirpath):
                        for filename in files:
                                filepath = os.path.join(root,filename)
                                pathlist.append(filepath)
        else:
                allobjects = os.listdir(dirpath)
                for f in allobjects:
                        thispath = os.path.join(dirpath,f)
                        if not os.path.isdir(thispath):
                                pathlist.append(thispath)
        return pathlist

def save_results(results,name=None,directory=None):
        """
        Standardised way of saving results in TXT files. Not sure what
        to do with them afterwards yet...
        """
        timestamp = str(datetime.now()).replace(" ","_").replace(":","")[0:21]
        # Truncates at milisecond level
        
        if not name:
                fname = "RESULTS_"+timestamp+".txt"
        else:
                fname = name+"_"+timestamp+".txt"
        
        if directory is None:
                current_dir = os.getcwd()
                outputdir = os.path.join(current_dir,"Results")
                if not os.path.exists(outputdir):
                        os.makedirs(outputdir)
        else:
                outputdir = directory
                if not os.path.exists(outputdir):
                        os.makedirs(outputdir)
        outpath = os.path.join(outputdir,fname)
        with open(outpath,'w') as txtfile:
                txtfile.write(results)
        return

def export_dicom_file(ds,outdir):
        """
        Export a DICOM dataset to the disk drive.
        At some point this will be customisable!
        """
        dir1 = str(ds.PatientName).replace('^','__')+"_"+remove_invalid_characters(ds.PatientID)
        dir2 = ds.StudyDate+"_"+ds.StudyTime
        dir3 = str(ds.SeriesNumber).zfill(4)+"_"+remove_invalid_characters(str(ds.SeriesDescription))
        
        #~ fname1 = str(ds.ImageType).replace('/','-').strip()+"_"
        fname1 = ''.join(str(i)+"_" for i in ds.ImageType)
        fname2 = str(ds.SeriesNumber).zfill(4)+"_"
        fname3 = str(ds.InstanceNumber).zfill(5)
        
        fext = '.DCM'
        
        outdirfull = os.path.join(outdir,dir1,dir2,dir3)
        if not os.path.exists(outdirfull):
                os.makedirs(outdirfull)
        
        ds.save_as(os.path.join(outdirfull,fname1+fname2+fname3+fext))
        return
        
def remove_invalid_characters(value):
        deletechars = '\\/:*?"<>|'
        for c in deletechars:
                value = value.replace(c,'')
        return value
