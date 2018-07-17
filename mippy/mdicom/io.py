import pickle as pickle
import os
import sys

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
