import mippy.dicom.reading as dcmread
import time
import sys
import os
import gc

threads = int(sys.argv[2])
nfiles = int(sys.argv[1])
print threads

directory = r'M:\MRI_Customers\Cobalt\ITM\QA\20170105-ITM-ACCEPTANCE\SortedImages'


print "Finding files"
files = dcmread.recursive_file_finder(directory)
print len(files)

uids = None
gc.collect()
print "STARTING MULTITHREADED READING"
start = time.time()
uids = dcmread.multidicomread(files[0:nfiles],threads)
print uids[-1]
end = time.time()
multi=end-start
print "MULTI",end-start,"seconds"
print "FINISHED MULTITHREADED READING"

#~ uids = None
#~ gc.collect()
#~ print "STARTING SINGLE FILES"
#~ start = time.time()
#~ uids = map(dcmread.get_instance_uid,files[0:nfiles])
#~ print uids[-1]
#~ end = time.time()
#~ single=end-start
#~ print "FINISHED SINGLE FILES"
#~ print "SINGLE",end-start,"seconds"

