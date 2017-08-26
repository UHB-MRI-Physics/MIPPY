from multiprocessing import Pool, cpu_count, freeze_support
import time
from contextlib import closing

def multithread(func,input,progressbar=None,threads=None):
	#~ freeze_support()
	if threads is None:
		threads=cpu_count()
	with closing( Pool(threads) ) as pool:
		result = pool.map_async(func,input,chunksize=1)
	while not result.ready():
		if not progressbar is None:
			progress = (float(len(input))-float(result._number_left))/float(len(input))*100.
			#~ print "PROGRESS", progress
			progressbar(progress)
		#~ print("num left: {}".format(result._number_left))
		time.sleep(0.1)
	progressbar(0.)
	pool.close()
	pool.join()
	return result.get()

