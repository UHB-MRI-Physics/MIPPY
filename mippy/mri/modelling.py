"""
Some useful stuff for modelling/fitting of MRI data
"""
import numpy as np
import scipy as sp
from scipy.optimize import curve_fit
from mippy.viewing import MIPPYImage
import datetime

def magnitude_inversion_recovery(t,T1,M0):
    return abs(M0 * (1 - 2* np.exp(-t/T1)))

def shmolli_t1_fit(images):
    """
    Given a 2D list of pydicom datasets sorted by inversion time, and provided
    with the inversion scheme (e.g. (5,1,1)), selectively use the inversion times
    to fit T1.

    Fitting:

    1. If range of values < 2*stdev, assume poor signal and reject (T1=0)
    2. Fit echoes from first inversion only to get T1_first
    3. Calculate difference in acquisition time between first image of first
       inversion and first image of second inversion to get Trec (recovery time)
    4. If T1_first >= RR, this is a "long T1".  T1 = T1_first.  [END FITTING]
    5. If T1_first < RR/4, this is "very short T1" - fit to only first 2 readouts from
       each inversion to get T1_early.  T1 = T1_early
    6. Else if T1_first > RR/4, include all echoes to get T1_full. T1 = T1_full
    7. Calculate R^2, and set T1=0 if R^2 too low (<90%)
    """

    inv_times = []
    acq_times = []
    rr_intervals = []
    inv_numbers = [0]*len(images)

    ### Determine inversion scheme
    # Collect timing data
    for image in images:
        datestamp = str(image.AcquisitionDate)
        timestamp = str(image.AcquisitionTime)
        YYYY = int(datestamp[0:4])
        MM = int(datestamp[4:6])
        DD = int(datestamp[6:8])
        hh = int(timestamp[0:2])
        mm = int(timestamp[2:4])
        ss = int(timestamp[4:6])
        uu = int(timestamp.split('.')[1])
        ta = datetime.datetime(YYYY,MM,DD,hh,mm,ss,uu)
        acq_times.append(ta)
        inv_times.append(float(image.InversionTime))
        rr_intervals.append(float(image.NominalInterval))

    # Calculate mean RR interval (should be consistent as nominal anyway)
    rr_mean = np.mean(rr_intervals)

    # For each image, see if inversion time is approximately 1 heartbeat after
    # any existing ones.  If it is, assume same inversion.  Use a 200ms window!
    # This loop will only work if images are sorted by inversion time.
    for i in range(len(images)):
        matched = False
        if i==0:
            inv_numbers[i]=1
            continue
        for j in range(i):
            if -200. < (inv_times[i]-inv_times[j]-rr_mean) < 200.:
                # Same inversion as inv_times[j]
                inv_numbers[i]=inv_numbers[j]
                print('{} matches {}'.format(i,j))
                matched = True
                break
        if not matched:
            print('{} not matched'.format(i))
            inv_numbers[i]=np.max(inv_numbers)+1

    # TESTING only
    # TI_init = 100.
    # TI_inc = 80.
    # inv_scheme = (5,1,1)
    # inv_numbers = [1,1,1,1,1,2,3]
    # inv_times = [TI_init,
    #             TI_init+rr_mean,
    #             TI_init+2*rr_mean,
    #             TI_init+3*rr_mean,
    #             TI_init+4*rr_mean,
    #             TI_init+TI_inc,
    #             TI_init+2*TI_inc]

    print(inv_times)
    print(inv_numbers)
    # print(acq_times)

    # Get 3D pixel array
    px_list = []
    for i in range(len(images)):
        im = MIPPYImage(images[i])
        px_list.append(im.px_float)

    im3d = np.array(px_list)
    dim = np.shape(im3d)

    # Fit for values from first inversion only
    T_rec = (acq_times[inv_numbers.index(2)]-acq_times[inv_numbers.index(1)]).total_seconds()*1000
    print('Trec {}'.format(T_rec))
    T_rec = rr_mean*6
    print('Trec {}'.format(T_rec))
    inv_times = np.array(inv_times)
    inv_numbers = np.array(inv_numbers)

    # Initialise T1 and M0 maps
    t1_map = np.zeros((dim[1],dim[2])).astype(np.float64)
    m0_map = np.zeros((dim[1],dim[2])).astype(np.float64)
    rsquare_map = np.zeros((dim[1],dim[2])).astype(np.float64)
    fine_fit_map = np.zeros((dim[1],dim[2])).astype(np.float64)
    fail_map = np.zeros((dim[1],dim[2])).astype(np.float64)

    signal_theshold = 0.5*np.median(im3d[im3d>0])

    n_prints = 0

    for y in range(dim[1]):
        if y%5==0:
            print('Fitting row {} of {}'.format(y+1,dim[1]))
        for x in range(dim[2]):

            init_T1 = 500
            init_M0 = 1000
            ydata = im3d[inv_numbers==1,y,x]
            if np.max(ydata)<signal_theshold or np.std(ydata)>np.mean(ydata):
                # Poor signal, ignore this pixel
                fail_map[y,x] = 1.
                continue
            xdata = inv_times[inv_numbers==1]
            try:
                popt,pcov = curve_fit(magnitude_inversion_recovery,xdata,ydata,[init_T1,init_M0])
                perr = np.sqrt(np.diag(pcov))
            except RuntimeError:
                # i.e. if fitting fails, leave at zero
                continue

            # Check whether this is long or short T1
            if popt[0]<rr_mean/3:   # Very short T1
                fine_fit_map[y,x]=1.
                # Take only first 2 readouts from each inversion
                indices = []

                for i in range(len(inv_numbers)):
                    if sum(inv_numbers[p]==inv_numbers[i] for p in indices)<3:
                        # If less than 2 indices pointing to this inversion inv_number...
                        indices.append(i)

                xdata = np.array([inv_times[p] for p in indices])
                ydata = im3d[indices,y,x]
                # if n_prints<3 and 100<y<156 and 100<x<156:
                #     print(indices)
                #     print(xdata)
                #     print(ydata)
                #     n_prints+=1
                try:
                    popt,pcov = curve_fit(magnitude_inversion_recovery,xdata,ydata,[init_T1,init_M0])
                    perr = np.sqrt(np.diag(pcov))
                except RuntimeError:
                    # i.e. if fitting fails, leave at zero
                    continue
            else:
                # Short-ish T1, re-fit with all echoes
                fine_fit_map[y,x]=2.
                ydata = im3d[:,y,x]
                xdata = inv_times
                try:
                    popt,pcov = curve_fit(magnitude_inversion_recovery,xdata,ydata,[init_T1,init_M0])
                    perr = np.sqrt(np.diag(pcov))
                except RuntimeError:
                    continue

            if popt[0]<perr[0]*2:
                # Less than 2 standard deviations, assume 0
                # Fail code 1
                fail_map[y,x] = 2.
                continue
            if popt[0]<0:
                # Negative T1 not feasible
                fail_map[y,x] = 3.
                continue
            # Calculate rsquare
            fit_data = magnitude_inversion_recovery(xdata,popt[0],popt[1])
            SS_res = np.sum((ydata-fit_data)**2)
            SS_tot = np.sum((ydata-np.mean(ydata))**2)
            rsquare = 1. - (SS_res/SS_tot)

            # Reject if rsquare<0.5
            if rsquare<0.7:
                # Fail code 3
                fail_map[y,x] = 4.
                rsquare_map[y,x] = rsquare
                continue



            # If all conditions above have failed, data is ok.  Add to maps.
            t1_map[y,x] = popt[0]
            m0_map[y,x] = popt[1]
            rsquare_map[y,x] = rsquare*100

    # Dump to text files to open in imagej
    np.savetxt(r'C:\dump\{}_t1.txt'.format(str(images[0].SeriesNumber).zfill(3)), t1_map)
    np.savetxt(r'C:\dump\{}_m0.txt'.format(str(images[0].SeriesNumber).zfill(3)), m0_map)
    np.savetxt(r'C:\dump\{}_rsquare.txt'.format(str(images[0].SeriesNumber).zfill(3)), rsquare_map)
    np.savetxt(r'C:\dump\{}_fine_fit.txt'.format(str(images[0].SeriesNumber).zfill(3)), fine_fit_map)
    np.savetxt(r'C:\dump\{}_fail.txt'.format(str(images[0].SeriesNumber).zfill(3)), fail_map)
