# -*- coding: utf-8 -*-
"""
Created on Tue Jan 03 12:30:07 2017

@author: rtfm
"""

import source.functions.rrpps_functions as rrpps
import numpy as np
	
db = rrpps.QADatabase()
#sites = db.get_sites()
#print sites
#print np.shape(sites)
#scanners,descriptions = db.get_scanners_at_site(sites[1])
#print scanners,descriptions
#coils = db.get_coils_on_scanner(scanners[0])
#print coils
scanners = db.get_scanners()
print scanners
sites = db.get_sites()
print sites
scanners_at_site,descriptions = db.get_scanners_at_site(sites[1])
print scanners_at_site
print descriptions

db.save_results(
	'QEH002','2012-05-12','8ch Head (4567)','SNR ACR COR',142.6,150
	)