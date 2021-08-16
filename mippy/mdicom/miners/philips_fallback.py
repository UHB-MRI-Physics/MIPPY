import pydicom
import numpy as np
from nibabel.nicom import csareader as csar
import json

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
    try:
        seq = dicom_ds.PulseSequenceName
        echo = dicom_ds.EchoPulseSequence
        multiple = dicom_ds.MultipleSpinEcho
    except AttributeError:
        try:
            # Buried in private tag sequence
            seq = dicom_ds[0x2005,0x140f][0].PulseSequenceName
            echo = dicom_ds[0x2005,0x140f][0].EchoPulseSequence
            multiple = dicom_ds[0x2005,0x140f][0].MultipleSpinEcho
        except KeyError:
            seq = dicom_ds[0x18,0x20].value

    type = dicom_ds.MRAcquisitionType

    val = ''

    if 'SE' in seq:
        val+='SE'
    elif 'T1TFE' in seq:
        val+='TGRE'
    elif 'FEEPI' in seq:
        val+='EPI GRE'

    if '2D' in type:
        val+=' 2D'
    elif '3D' in type:
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
        return ",".join(str(dim) for dim in fov)
    except:
        pxspc_x = dicom_ds.PixelSpacing[0]
        pxspc_y = dicom_ds.PixelSpacing[1]
        rows = dicom_ds.Rows
        cols = dicom_ds.Columns
        fov = str(int(np.round(pxspc_x*cols,0)))+","+str(int(np.round(pxspc_y*rows,0)))
        return fov

def get_acq_matrix(dicom_ds):
    try:
        matrix = dicom_ds.AcquisitionMatrix
    except AttributeError:
        # AcquisitionMatrix tag doesn't exist. Need to
        # work it out from other tags.
        phase = dicom_ds.InPlanePhaseEncodingDirection
        freq_steps = dicom_ds[0x18,0x9058].value
        phase_steps = dicom_ds[0x18,0x9231].value
        phase_3d = dicom_ds[0x18,0x9232].value
        if phase=='ROW':
            matrix = str(phase_steps)+','+str(freq_steps)
            return matrix
        elif phase=='COLUMN':
            matrix = str(freq_steps)+','+str(phase_steps)
            return matrix

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
    matrix = [int(a) for a in get_acq_matrix(dicom_ds).split(',')]
    phase_encode = dicom_ds.InPlanePhaseEncodingDirection
    try:
        # Can't remember which versio of Philips headers this works in, but left
        # in for prosperity
        kspace_lines = dicom_ds[0x2005,0x140f].value[0][0x18,0x9093].value
    except KeyError:
        try:
            # Missing tag. This should work in Philips release 5 scanners...
            kspace_lines = float(dicom_ds[0x18,0x9093].value)
        except KeyError:
            # Use number of phase encoding steps
            kspace_lines = float(dicom_ds[0x18,0x89].value)
    # print(matrix)
    # print(kspace_lines)
    if phase_encode=='ROW':
        oversampling=kspace_lines/float(matrix[0])-1
    elif phase_encode=='COL' or phase_encode=='COLUMN':
        oversampling=kspace_lines/float(matrix[1])-1

    return float(oversampling)

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
    return np.round(float(dicom_ds.RepetitionTime),3)

def get_TE(dicom_ds):
    try:
        return np.round(float(dicom_ds.EchoTime),3)
    except:
        # Use effective echo time (copied from from per-frame group to create single slice)
        return np.round(dicom_ds.EffectiveEchoTime,3)

def get_TI(dicom_ds):
    try:
        return np.round(float(dicom_ds.InversionTime),3)
    except AttributeError:
        #print("No inversion time found")
        return "None"

def get_flip_angle(dicom_ds):
    return float(dicom_ds.FlipAngle)

def get_pat_type(dicom_ds):
    #print("PAT NOT YET SUPPORTED")
    try:
        parallel = dicom_ds[0x2005,0x140f][0].ParallelAcquisition
        if parallel == "YES":
            pat = dicom_ds[0x2005,0x140f][0].ParallelAcquisitionTechnique
        else:
            pat = "NONE"
        return pat
    except KeyError:
        return "UNKNOWN"
    # except:
    #     print("Could not read ParallelAcquisitionTechnique tags")
    #     return "UNKNOWN"

def get_pat_2d(dicom_ds):
    # print("PAT NOT YET SUPPORTED")
    # Test if EPI
    seq = get_sequence_type(dicom_ds)
    pat = get_pat_type(dicom_ds)

    if pat=="UNKNOWN":
        return "UNKNOWN"

    if not pat=="NONE":
        try:
            pat_factor = dicom_ds[0x2005,0x140f][0].ParallelReductionFactorInPlane
            return pat_factor
        except:
            print("Couldn't read pat factor tag")
            if 'EPI' in seq:
                etl = dicom_ds.EchoTrainLength
                pe_steps = dicom_ds.NumberOfPhaseEncodingSteps
                print("ETL: {}\nPE_STEPS: {}".format(etl,pe_steps))

                pat_factor = int(np.round(pe_steps/etl,0))
                print("PAT_FACTOR: {}".format(pat_factor))

                return pat_factor
            else:
                return "UNKNOWN"
    else:
        return 1.

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
        print("Coil elements not supported yet for Philips")
        return "UNKNOWN"

# Some comprehension of coil string required.
# Assume something of the fashion C:HE1-4;SP3;SP5
def read_coil_string(coilstring):
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
    return active_coils

def get_bandwidth(dicom_ds):
    return float(dicom_ds.PixelBandwidth)

def get_image_filter(dicom_ds):
    filtering = ''
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
        syncra = dicom_ds[0x2005,0x10a1].value
    except KeyError:
        syncra = ''
    imtype = dicom_ds.ImageType
    clear = False
    sense = False

    if 'COCA' in syncra or 'CLEAR' in imtype:
        clear = True
    elif 'CLASSIC' in syncra or syncra=='':
        clear = False
    elif 'SENSE' in syncra:
        sense=True

    if clear or sense:
        # If SENSE active, CLEAR must be on
        return 'CLEAR'
    else:
        # This won't catch "other" types of normalisation, such as body tuned etc.  They will
        # probably all be lumped in with CLEAR.
        return 'None'

def get_distortion_correction(dicom_ds):
    try:
        dc_tag = dicom_ds[0x2005,0x10a9].value
    except KeyError:
        dc_tag = None

    dc_filter_type = 'UNKNOWN'

    if type(dc_tag)==bytes:
        dc_tag = dc_tag.decode('UTF-8')

    if str(dc_tag)==str('NONE'):
        dc_filter_type = 'None'
    elif str(dc_tag)=='2D':
        dc_filter_type = '2D'
    elif str(dc_tag)=='3D':
        dc_filter_type = '3D'

    return dc_filter_type

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
