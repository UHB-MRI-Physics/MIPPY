# Generic functions for MIPPY windows that don't fit anywhere else

def optionmenu_patch(om, var):
        menu = om['menu']
        last = menu.index("end")
        for i in range(0, last+1):
                menu.entryconfig(i, variable=var)

from collections import Mapping, Container
from sys import getsizeof

def deep_getsizeof(o, ids): 
        # From https://code.tutsplus.com/tutorials/understand-how-much-memory-your-python-objects-use--cms-25609
        """Find the memory footprint of a Python object

        This is a recursive function that drills down a Python object graph
        like a dictionary holding nested dictionaries with lists of lists
        and tuples and sets.

        The sys.getsizeof function does a shallow size of only. It counts each
        object inside a container as pointer only regardless of how big it
        really is.

        :param o: the object
        :param ids:
        :return:
        """
        d = deep_getsizeof
        if id(o) in ids:
                return 0

        r = getsizeof(o)
        ids.add(id(o))

        if isinstance(o, str) or isinstance(0, str):
                return r

        if isinstance(o, Mapping):
                return r + sum(d(k, ids) + d(v, ids) for k, v in o.items())

        if isinstance(o, Container):
                return r + sum(d(x, ids) for x in o)

        return r
        
def getsizeof(an_object):
        from pympler import asizeof
        return asizeof.asizeof(an_object)