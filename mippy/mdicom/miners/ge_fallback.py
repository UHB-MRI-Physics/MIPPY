import pydicom
import numpy as np
from nibabel.nicom import csareader as csar
import json

def get_serial_number(dicom_ds):
    return str(dicom_ds.DeviceSerialNumber)

def get_patient_name(dicom_ds):
    #print('\nPATIENT NAME = ',str(dicom_ds.PatientName))
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

    seq = dicom_ds.ScanningSequence
    var = dicom_ds.SequenceVariant

    seqtype = dicom_ds.MRAcquisitionType

    val = ''

    if 'EP' in seq:
        val+='EPI'
        if 'GR' in seq:
            val+=' GRE'
        elif 'SE' in seq:
            val+=' SE'
    elif 'SE' in seq:
        val+='SE'
    elif 'GR' in seq:
        val+='GRE'

    if '2D' in seqtype.upper():
        val+=' 2D'
    elif '3D' in seqtype.upper():
        val+=' 3D'

    if len(val)>0:
        return val
    else:
        print("Couldn't detect sequence type")
        return "UNKNOWN"

def get_fov(dicom_ds):

    try:
        fov = dicom_ds[0x51,0x100c].value
        fov = fov.split(" ")[1]
        fov = fov.split("*")
        #print('\nFOV = ',",".join(str(dim) for dim in fov))
        return ",".join(str(dim) for dim in fov)
    except:
        pxspc_x = dicom_ds.PixelSpacing[0]
        pxspc_y = dicom_ds.PixelSpacing[1]
        rows = dicom_ds.Rows
        cols = dicom_ds.Columns
        fov = str(int(np.round(pxspc_x*cols,0)))+","+str(int(np.round(pxspc_y*rows,0)))
        #print('\nFOV = ',fov)
        return fov

def get_acq_matrix(dicom_ds):
    matrix = dicom_ds.AcquisitionMatrix
    # This needs explanation!
    # You get a 4-long list of values, in this order.
    # [ FREQ-ROWS, FREQ-COLS, PHASE-ROWS, PHASE-COLS ]
    # So if you phase encode by column, you'll get
    # [ VALUE, zero, zero, VALUE ]
    # And if you phase encode by row, you'll get
    # [ zero, VALUE, VALUE, zero ]
    if not matrix[0]==0:
        # Column phase encoding
        # Row in [0], Column in [3]
        matrix = str(matrix[0])+','+str(matrix[3])
        return matrix
    else:
        # Row phase encoding
        # Row in [2], Column in [1]
        matrix = str(matrix[2])+','+str(matrix[1])
        return matrix

def get_recon_matrix(dicom_ds):
    rows = dicom_ds.Rows
    cols = dicom_ds.Columns
    return str(cols)+','+str(rows)

def get_acq_slice_thickness(dicom_ds):
    if dicom_ds.MRAcquisitionType=='2D':
        return float(dicom_ds.SliceThickness)
    elif dicom_ds.MRAcquisitionType=='3D':
        try:
            slice_resolution = dicom_ds[0x19,0x1017].value
            slice_thickness = dicom_ds.SliceThickness
            if slice_resolution<1:
                acq_slice_thickness = slice_thickness / slice_resolution
                return float(acq_slice_thickness)
            else:
                return float(slice_thickness)
        except KeyError:
            print("Cannot read slice resolution tag")
            return "UNKNOWN"
    else:
        print("Do not understand acquisition acquisition type")
        return "UNKNOWN"

def get_recon_slice_thickness(dicom_ds):
    return float(dicom_ds.SliceThickness)

def get_oversampling(dicom_ds):
    print("Oversmapling not yet supported for GE")
    return "UNKNOWN"

def get_phase_encode_direction(dicom_ds):
    orient = get_image_orientation(dicom_ds)
    phase = dicom_ds.InPlanePhaseEncodingDirection
    if orient=='TRA':
        if phase=='ROW':
            return 'RL'
        elif phase=='COL' or phase=='COLUMN':
            return 'AP'
        else:
            print("Do not understand phase encode direction")
            return "UNKNOWN"
    elif orient=='SAG':
        if phase=='ROW':
            return 'AP'
        elif phase=='COL' or phase=='COLUMN':
            return 'FH'
        else:
            print("Do not understand phase encode direction")
            return "UNKNOWN"
    elif orient=='COR':
        if phase=='ROW':
            return 'RL'
        elif phase=='COL' or phase=='COLUMN':
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
    #print('\nTR = ',dicom_ds.RepetitionTime)
    return float(dicom_ds.RepetitionTime)

def get_TE(dicom_ds):
    #print('\nTE = ',dicom_ds.EchoTime,'\n')
    return float(dicom_ds.EchoTime)

def get_TI(dicom_ds):
    try:
        return float(dicom_ds.InversionTime)
    except AttributeError:
        # print("No inversion time found")
        return "None"

def get_flip_angle(dicom_ds):
    return float(dicom_ds.FlipAngle)

def get_pat_type(dicom_ds):
    # print("PAT NOT YET SUPPORTED")
    return "UNKNOWN"

def get_pat_2d(dicom_ds):
    # print("PAT NOT YET SUPPORTED")
    return "UNKNOWN"

def get_pat_3d(dicom_ds):
    # print("PAT NOT YET SUPPORTED")
    return "UNKNOWN"

def get_partial_fourier_phase(dicom_ds):
    # print("PARTIAL FOURIER NOT YET SUPPORTED")
    return "UNKNOWN"

def get_partial_fourier_slice(dicom_ds):
    # print("PARTIAL FOURIER NOT YET SUPPORTED")
    return "UNKNOWN"

def get_coil_elements(dicom_ds):
    try:
        coil = dicom_ds[0x18,0x1250].value
        return coil
    except KeyError:
        print("Coil type not detected")
        return "UNKNOWN"

# Some comprehension of coil string required.
# Assume something of the fashion C:HE1-4;SP3;SP5
def read_coil_string(coilstring):
    #print('\nread_coil_string function is being called')
    coils = coilstring.replace('C:','').split(';')
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
        else:
            active_coils.append(coil)
    #print('\nACTIVE COILS = ',active_coils)
    return active_coils

def get_bandwidth(dicom_ds):
    return float(dicom_ds.PixelBandwidth)

def get_image_filter(dicom_ds):
    filtering = 'UNKNOWN'

    print("Filtering/post-processing not yet supported for GE")
    return filtering

    # Currently redundant code...
    try:
        filtering = dicom_ds[0x18,0x9064].value
    except KeyError:
        # Tag is within a private sequence?
        try:
            filtering = dicom_ds[0x2005,0x140f][0][0x18,0x9064].value
        except KeyError:
            # Can't find kspace filter tag, assume none applied
            filtering = 'NONE'
    if not filtering == 'NONE':
        return 'ImageFilter-PostProc'
    else:
        return 'None'

def get_uniformity_correction(dicom_ds):
    try:
        filter_mode = dicom_ds[0x43,0x102d].value
    except KeyError:
        # No filtering applied
        return 'None'

    if filter_mode == 'p+':
        return 'PURE'
    elif filter_mode == 's':
        return 'SCIC'
    else:
        print('GE filter mode (0043,102d) not understood')
        return 'UNKNOWN'



def get_distortion_correction(dicom_ds):
    print('Assuming 2D correction by default for GE')
    return '2D'

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
        "UNKNOWN"

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

