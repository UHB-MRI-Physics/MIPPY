from multiprocessing import Pool, cpu_count, freeze_support
import time

def multithread(func,input,progressbar=None,threads=None):
	#~ freeze_support()
	if threads is None:
		threads=cpu_count()
	pool = Pool(threads)
	result = pool.map_async(func,input,chunksize=1)
	while not result.ready():
		if not progressbar is None:
			progressbar((float(len(input))-float(result._number_left))/len(input)*100)
		#~ print("num left: {}".format(result._number_left))
		time.sleep(0.1)
	progressbar(0.)
	pool.close()
	pool.join()
	return result.get()

