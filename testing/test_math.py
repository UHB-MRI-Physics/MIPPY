from mippy.math import *

def test_intround():
	a = 1.4
	b = 6.7
	c = 976.4278
	assert intround(a) == int(1)
	assert intround(b) == int(7)
	assert intround(c) == int(976)