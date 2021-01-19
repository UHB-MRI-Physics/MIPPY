from multiprocessing import Pool, cpu_count, freeze_support
import time
from contextlib import closing
import sys

def multithread(func,input,progressbar=None,threads=None):
        #~ freeze_support()
        if threads is None:
                threads=int(cpu_count())+1
        pool = Pool(threads)
        print("Running on {} threads".format(threads))
        result = pool.map_async(func,input,chunksize=1)
        while not result.ready():
                if not progressbar is None:
                        progress = (float(len(input))-float(result._number_left))/float(len(input))*100.
                        #~ print "PROGRESS", progress
                        progressbar(progress)
                #~ print("num left: {}".format(result._number_left))
                time.sleep(0.1)
        if not progressbar is None:
                progressbar(0.)
        print("Closing multiprocessing pool")
        pool.close()
        print("Joining pool")
        pool.join()
        print("Fetching pool results")
        return result.get()
