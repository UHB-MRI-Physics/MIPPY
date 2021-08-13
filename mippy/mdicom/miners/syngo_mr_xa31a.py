from mippy.mdicom.siemens import get_ascconv
import pydicom
import numpy as np
from nibabel.nicom import csareader as csar
import json

def get_ascii_value(dicom_ds,searchterm):
    if not ascii in dir(dicom_ds):
        asc = get_ascconv(dicom_ds)
        setattr(dicom_ds,'ascii',asc)
    else:
        print("Using saved ASCII")
    return_value = None
    #~ header = self.get_ascconv()
    found = False
    for s in dicom_ds.ascii:
        if searchterm in s[0]:
            return_value = s[1]
            found = True
            break
    if not found:
        return None
    else:
        try:
            return_value = float(return_value)
        except:
            pass
    return return_value

def is_number(s):
    """
    Tests if a string is readable as a number
    """
    try:
        float(s)
    except ValueError:
        return False
    return True

def get_serial_number(dicom_ds):
    return str(dicom_ds.DeviceSerialNumber)

def get_patient_name(dicom_ds):
    return str(dicom_ds.PatientName)

def get_image_orientation(dicom_ds):
    orient = dicom_ds.ImageOrientationPatient
    # Check TRA
    if ( abs(orient[0])>abs(orient[1]) and abs(orient[0])>abs(orient[2])
        and abs(orient[4])>abs(orient[3]) and abs(orient[4])>abs(orient[5])):
            return "TRA"
    # Check SAG
    elif ( abs(orient[1])>abs(orient[0]) and abs(orient[1])>abs(orient[2])
        and abs(orient[5])>abs(orient[3]) and abs(orient[5])>abs(orient[4])):
            return "SAG"
    # Check COR
    elif ( abs(orient[0])>abs(orient[1]) and abs(orient[0])>abs(orient[2])
        and abs(orient[5])>abs(orient[3]) and abs(orient[5])>abs(orient[4])):
            return "COR"
    else:
        print("ORIENTATION NOT DETECTED", orient)
        return "UNKNOWN"

def get_sequence_type(dicom_ds):
    seq = dicom_ds[0x18,0x9005].value
    if "se2d" in seq:
        return "SE 2D"
    elif "epfid2d" in seq:
        return "EPI GRE 2D"
    elif "ep2d_diff" in seq:
        return "EPI DIFF 2D"
    elif "ep2d_se" in seq:
        return "EPI SE 2D"
    elif "fl2d" in seq:
        return "GRE 2D"
    elif "fl3d" in seq:
        return "GRE 3D"
    elif "tse2d" in seq:
        return "TSE 2D"
    elif "tse3d" in seq:
        return "TSE 3D"
    elif "tfl2d" in seq:
        return "TGRE 2D"
    elif "tfl3d" in seq:
        return "TGRE 3D"
    else:
        print("SEQUENCE NOT DETECTED", seq)
        return "UNKNOWN"

def get_fov(dicom_ds):
    pxspc_x = dicom_ds.PixelSpacing[0]
    pxspc_y = dicom_ds.PixelSpacing[1]
    rows = dicom_ds.Rows
    cols = dicom_ds.Columns
    fov = str(int(np.round(pxspc_x*cols,0)))+","+str(int(np.round(pxspc_y*rows,0)))
    return fov

def get_acq_matrix(dicom_ds):
    # This does not take account of partial fourier. I don't know whether the
    # effects of partial fourier are already included in phase encode lines, or
    # if this is number of lines before applying PF ???
    base_resolution = int(np.round(get_ascii_value(dicom_ds,'sKSpace.lBaseResolution'),0))
    phase_encode_lines = int(np.round(get_ascii_value(dicom_ds,'sKSpace.lPhaseEncodingLines'),0))
    phase = dicom_ds.InPlanePhaseEncodingDirection
    if phase=='ROW':
        matrix = str(phase_encode_lines)+','+str(base_resolution)
        return matrix
    elif phase=='COLUMN':
        matrix = str(base_resolution)+','+str(phase_encode_lines)
        return matrix

def get_recon_matrix(dicom_ds):
    rows = dicom_ds.Rows
    cols = dicom_ds.Columns
    return str(cols)+','+str(rows)

def get_acq_slice_thickness(dicom_ds):
    if dicom_ds.MRAcquisitionType=='2D':
        return float(dicom_ds.SliceThickness)
    elif dicom_ds.MRAcquisitionType=='3D':
        slice_resolution = get_ascii_value(dicom_ds,'sKSpace.dSliceResolution')
        slice_thickness = dicom_ds.SliceThickness
        if slice_resolution<1.:
            acq_slice_thickness = slice_thickness / slice_resolution
            return float(acq_slice_thickness)
        else:
            return float(slice_thickness)
    else:
        print("Do not understand acquisition acquisition type")
        return "UNKNOWN"

def get_oversampling(dicom_ds):
    # Do not know how this tag actually presents. Expect errors if you have
    # images with oversampling on.
    oversampling = dicom_ds.OversamplingPhase
    if oversampling=='NONE':
        oversampling = None

    if not oversampling is None:
        return float(oversampling)
    else:
        # Assume no oversampling if tag not written
        return 0.

def get_recon_slice_thickness(dicom_ds):
    return float(dicom_ds.SliceThickness)

def get_phase_encode_direction(dicom_ds):
    orient = get_image_orientation(dicom_ds)
    phase = dicom_ds.InPlanePhaseEncodingDirection
    if orient=='TRA':
        if 'ROW' in phase:
            return 'RL'
        elif 'COL' in phase:
            return 'AP'
        else:
            print("Do not understand phase encode direction")
            return "UNKNOWN"
    elif orient=='SAG':
        if 'ROW' in phase:
            return 'AP'
        elif 'COL' in phase:
            return 'FH'
        else:
            print("Do not understand phase encode direction")
            return "UNKNOWN"
    elif orient=='COR':
        if 'ROW' in phase:
            return 'RL'
        elif 'COL' in phase:
            return 'FH'
        else:
            print("Do not understand phase encode direction")
            return "UNKNOWN"
    else:
        print("Do not understand orientation")
        return "UNKNOWN"

def get_nsa(dicom_ds):
    return float(dicom_ds.NumberOfAverages)

def get_TR(dicom_ds):
    return float(dicom_ds.RepetitionTime)

def get_TE(dicom_ds):
    try:
        return np.round(float(dicom_ds.EchoTime),3)
    except:
        # Use effective echo time (copied from from per-frame group to create single slice)
        # XA20 seems to write this instead of actual echo time...
        return np.round(dicom_ds.EffectiveEchoTime,3)

def get_TI(dicom_ds):
    try:
        return float(dicom_ds.InversionTime)
    except AttributeError:
#            print("No inversion time found")
        return "None"

def get_flip_angle(dicom_ds):
    return float(dicom_ds.FlipAngle)

def get_pat_type(dicom_ds):
#        print("PAT NOT YET SUPPORTED")
    return "UNKNOWN"

def get_pat_2d(dicom_ds):
#        print("PAT NOT YET SUPPORTED")
    return "UNKNOWN"

def get_pat_3d(dicom_ds):
#        print("PAT NOT YET SUPPORTED")
    return "UNKNOWN"

def get_partial_fourier_phase(dicom_ds):
#        print("PARTIAL FOURIER NOT YET SUPPORTED")
    phase_partial_fourier = get_ascii_value(dicom_ds,'sKSpace.ucPhasePartialFourier')/16
    return phase_partial_fourier

def get_partial_fourier_slice(dicom_ds):
#        print("PARTIAL FOURIER NOT YET SUPPORTED")
    slice_partial_fourier = get_ascii_value(dicom_ds,'sKSpace.ucSlicePartialFourier')/16
    return slice_partial_fourier

def get_coil_elements(dicom_ds):
    try:
        coilstring = str(dicom_ds[0x51,0x100f].value)
    except KeyError:
        # Attempt alternative DICOM tag for newer scanners
        try:
            coilstring = str(dicom_ds[0x21,0x114f].value)
        except KeyError:
            # Still didn't work
            print("Unable to get coil information")
            return "UNKNOWN"

    coils = read_coil_string(coilstring)
    return ';'.join(coils)



# Some comprehension of coil string required.
# Assume something of the fashion C:HE1-4;SP3;SP5
def read_coil_string(coilstring):
    coils = coilstring.replace('b\'C:','').replace('C:','').replace('\'','').strip().split(';')
    active_coils = []
    for coil in coils:
        if '-' in coil:
            # Convert range into list of individual elements
            # Get prefix
            prefix = ''
            for char in coil:
                if not is_number(char):
                    prefix=prefix+char
                else:
                    break
            # Remove prefx and split at dash
            coil_range = coil.replace(prefix,'').split('-')
            for i in range(int(coil_range[0]),int(coil_range[1])+1):
                active_coils.append(prefix+str(i))
        elif ',' in coil:
            # Convert range into list of individual elements
            # Get prefix
            prefix = ''
            for char in coil:
                if not is_number(char):
                    prefix=prefix+char
                else:
                    break
            # Remove prefix and split at comma
            coil_range = coil.replace(prefix,'').split(',')
            for num in coil_range:
                active_coils.append(prefix+num)
        else:
            active_coils.append(coil)
    return active_coils

def get_bandwidth(dicom_ds):
    return float(dicom_ds.PixelBandwidth)

def get_image_filter(dicom_ds):
    filters = []
    imfilter_on = get_ascii_value(dicom_ds,'sImageFilter.ucOn')
    rawfilter_on = get_ascii_value(dicom_ds,'sRawFilter.ucOn')
    ellipticalfilter_on = get_ascii_value(dicom_ds,'sEllipticalFilter.ucOn')
    b1filter_on = get_ascii_value(dicom_ds,'sBiFiCFilter.ucOn')
    if imfilter_on =='0x1':
        filters.append("ImageFilter")
    if rawfilter_on == '0x1':
        rawfilter_value = int(np.round(get_ascii_value(dicom_ds,'sRawFilter.lSlope_256'),0))
        filters.append(f"RawFilter{rawfilter_value}")
    if ellipticalfilter_on == '0x1':
        ellipticalfilter_mode = get_ascii_value(dicom_ds,'sEllipticalFilter.ucMode')
        if ellipticalfilter_mode == 1:
            filters.append("EllipticalFilter2D")
        elif ellipticalfilter_mode == 2:
            filters.append("EllipticalFilter3D")
    if b1filter_on == '0x1':
        # B1 filter mode available, but not understood so not included yet
        filters.append("B1Filter")
    if len(filters)>0:
        return ';'.join(filters)
    else:
        return 'None'

def get_uniformity_correction(dicom_ds):
    imtype = dicom_ds[0x21,0x1175].value
    # Appears to be a private version of legacy ImageType tag. Will do the job for now
    # and actually appears to be only difference between filtered and unfiltered images
    if 'NORM' in imtype:
        this_image_norm = True
    else:
        this_image_norm = False
    prescan = get_ascii_value(dicom_ds,'sPreScanNormalizeFilter.ucOn')
    norm_filt = get_ascii_value(dicom_ds,'sNormalizeFilter.ucOn')
    prescan_mode = get_ascii_value(dicom_ds,'sPreScanNormalizeFilter.ucMode')
    if prescan is None:
        prescan_on = False
    elif prescan == '0x1':
        prescan_on = True
    else:
        # Assume if tag exists, it's on.
        prescan = True
    if norm_filt is None:
        norm_on = False
    elif norm_filt == '0x1':
        norm_on = True
    else:
        # Assume if tag exists, it's on
        norm_filt = True

    filters = ""
    if prescan_on:
        filters+="PreScanNormalize"
        if prescan_mode==1: # Moderate mode
            filters+="-Moderate"
        elif prescan_mode==2: # Normal mode
            filters+="-Normal"
        elif prescan_mode==4: # Broad mode
            filters+="-Broad"
        if not this_image_norm:
            filters+="-Unfiltered"
    elif norm_on:
        filters+="Normalize"
        # Lots of potential modes/settings for this but not sure what they are
        if not this_image_norm:
            filters+="-Unfiltered"
    else:
        filters+='None'
    return filters

def get_distortion_correction(dicom_ds):
    imtype = dicom_ds[0x21,0x1175].value
    # Appears to be a private version of legacy ImageType tag. Will do the job for now
    # and actually appears to be only difference between filtered and unfiltered images
    if 'DIS2D' in imtype:
        this_image_dc = '2D'
    elif 'DIS3D' in imtype:
        this_image_dc = '3D'
    else:
        this_image_dc = False

    try:
        # Fudge for XA data - tags unfiltered images as DISTORTED
        if dicom_ds[0x8,0x9206].value=='DISTORTED':
            this_image_dc = False
        else:
            this_image_dc = True
    except:
        pass

    dc_filter = get_ascii_value(dicom_ds,'sDistortionCorrFilter.ucMode')
    if dc_filter == '0x2':
        dc_filter_type = '2D'
    elif dc_filter == '0x4':
        dc_filter_type = '3D'
    elif dc_filter == 2:
        dc_filter_type = '2D'
    elif dc_filter == 3 or dc_filter == 4:
        dc_filter_type = '3D'
    else:
        dc_filter_type = False

    if dc_filter_type and this_image_dc:
        return dc_filter_type
    elif dc_filter_type and not this_image_dc:
        return dc_filter_type+'-Unfiltered'
    else:
        return "None"

def get_study_uid(dicom_ds):
    return str(dicom_ds.StudyInstanceUID)

def get_series_number(dicom_ds):
    return dicom_ds.SeriesNumber

def get_series_uid(dicom_ds):
    return str(dicom_ds.SeriesInstanceUID)

def get_instance_number(dicom_ds):
    return dicom_ds.InstanceNumber

def get_sop_uid(dicom_ds):
    return str(dicom_ds.SOPInstanceUID)

def get_study_date(dicom_ds):
    return str(dicom_ds.StudyDate)

def get_study_time(dicom_ds):
    return str(dicom_ds.StudyTime)

def get_institution_name(dicom_ds):
    try:
        return str(dicom_ds.InstitutionName)
    except:
        return "UNKNOWN"

def get_scanner_model(dicom_ds):
    return str(dicom_ds.Manufacturer)+' '+str(dicom_ds.ManufacturerModelName)

def get_institution_address(dicom_ds):
    return str(dicom_ds.InstitutionAddress)

def get_department(dicom_ds):
    try:
        return str(dicom_ds.InstitutionalDepartmentName)
    except AttributeError:
        return "UNKNOWN"

def get_station_name(dicom_ds):
    return str(dicom_ds.StationName)

def get_field_strength(dicom_ds):
    return float(dicom_ds.MagneticFieldStrength)
