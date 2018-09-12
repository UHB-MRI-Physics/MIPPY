import pydicom
from nibabel.nicom import csareader as csar

def get_ascii_header(ds):
        """
        Expects a pydicom dataset.
        Uses nibabel's "nicom" module to extract CSA data
        """
        csa = csar.get_csa_header(ds,'series')
        try:
                csa_header = csa['tags']['MrPhoenixProtocol']['items'][0]
        except TypeError:
                csa_header = csa['tags']['MrProtocol']['items'][0]
        
        return csa_header

def get_ascconv(ds):
        ascii = get_ascii_header(ds)
        start_string = '### ASCCONV BEGIN'
        end_string = 'ASCCONV END ###'
        ascconv = ascii[ascii.find(start_string):ascii.find(end_string)+len(end_string)].split('\n')
        asc_split = []
        for i in range(len(ascconv)-1):
                if i == 0:
                        continue
                asc_split.append(ascconv[i].replace(' ','').replace('\t','').split('='))
        #~ for i in range(10):
                #~ print asc_split[i]
        return asc_split
        