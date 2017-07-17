from multiprocessing.dummy import Pool, cpu_count
import time

def multithread(func,input,progressbar=None):
	pool = Pool(cpu_count()*3)
	#~ pool = Pool()
	result = pool.map_async(func,input,chunksize=1)
	while not result.ready():
		if not progressbar is None:
			progressbar((float(len(input))-float(result._number_left))/len(input)*100)
		#~ print("num left: {}".format(result._number_left))
		time.sleep(0.25)
	progressbar(0.)
	pool.close()
	pool.join()
	return result.get()

