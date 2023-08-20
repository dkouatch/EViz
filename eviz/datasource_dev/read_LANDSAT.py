"""
Author:
Date: 25-07-2022

The purpose of this file is to define the functions necessary to read a file of a collection of Landsat satellite
data and convert it into an XArray Dataset object.

File Collection: LANDSAT Satellite
File Format: HDF4
File-Reading Package: PyHDF
File Naming Conventions:
    LXS PPPRRR YYYYDDD GSIVV

    - - Information about what type of satellite and sensor
    L = Landsat
    X = Sensor
        'C' = OLI & IRS
        'O' = OLI only
        'I' = IRS only
        'E' = ETM+
        'T' = TM
        'M' = MSS
    S = Satellite
        '8' = Landsat-8
        '7' = Landsat-7
        ...
        '1' = Landsat-1

    - - Swath location on Earth using Worldwide Reference System (WRS)
    PPP -> WRS path
    RRR -> WRS row

    - - Date of swath acquisition using Julian calendar (# of days in year starting on Jan. 1)
    YYYY -> year of acquisition
    DDD -> Julian day of year

    - - How the data was received by a ground station
    GSI -> Ground station identifier
    VV -> Archive version number

    ex. LT50830152011198GLC00.hdf
        • Landsat-5 TM
        • WRS Path: 083; WRS Row: 015
        • Acquisition Date: July 17, 2011
        • Gilmore Creek ground station at NOAA facility near Fairbanks, Alaska

"""

# I. IMPORT STATEMENTS - - - - - - -
import numpy as np
import xarray as xr
from pyhdf.SD import SD, SDC


# II. ACCESSOR & HELPER METHODS - - - - - - -
def get_fid(filename):
    """
    Accesses the file reader object for a file given its name
    :param filename: a String of a file's full path
    :return: a file reader (SD) object
    """

    fid = SD(filename, SDC.READ)
    return fid

# - - - - - A. Data Restoration
def get_fill(ds):
    """
    Returns the fill value of a given dataset (SDS) object
    :param ds: an SDS object
    :return: float, int, or 'None'
    """

    for key, value in ds.attributes().items():
        if key == '_FillValue':
            return value
    return None

def get_scale(ds):
    """
    Returns the scale factor of a given dataset (SDS) object
    :param ds: an SDS object
    :return: float, int, or 1
    """

    for key, value in ds.attributes().items():
        if key == 'scale_factor':
            return value
    return 1

def get_offset(ds):
    """
    Returns the offset value of a given dataset (SDS) object
    :param ds: an SDS object
    :return: float, int, or 0
    """

    for key, value in ds.attributes().items():
        if key == 'add_offset':
            return value
    return 0

def restore_data(ds):
    """
    Restores the data o a given dataset (SDS) object
    :param ds: an SDS object
    :return: a NumPy array
    """

    fill = get_fill(ds)
    scale = get_scale(ds)
    offset = get_offset(ds)

    data = ds.get()  # .astype('float')

    data = np.where(data != fill, data, np.nan)   # fill
    data *= scale   # scale
    data += offset   # offset

    return data

# - - - - - B. Dimensions
def get_dims(ds):
    """
    Returns the dimension (SDim) objects of a given dataset (SDS) object
    :param ds: an SDS object
    :return: a Python list of SDim objects
    """

    dims = []  # Will actually hold dimension objects

    for i in range(len(ds.dimensions())):
        dims.append(ds.dim(i))

    return dims

def get_dim_attrs(dim):
    """
    Returns the attributes of a given dimension (SDim) object
    :param dim: an SDim object
    :return: a Python dictionary (String keys and values)
    """

    attrs = {}  # Will hold dim attrs

    attrs['Name'] = dim.info()[0]
    attrs['dtype'] = dim.info()[2]
    attrs.update(dim.attributes())  # Adds other unknown attributes

    return attrs


def get_dims_attrs(ds):
    """
    Returns the dimension attributes for a given dataset (SDS) object
    :param ds: an SDS object
    :return: a Python dictionary of String keys and dictionary values
    """
    dims_attrs = {}
    dims = get_dims(ds)

    for dim in dims:
        if dim.info()[0] == 'YDim':
            dims_attrs['lat'] = get_dim_attrs(dim)
        elif dim.info()[0] == 'XDim':
            dims_attrs['lon'] = get_dim_attrs(dim)

    return dims_attrs

# - - - - - C. Coordinates
def check_fid_coords(fid):
    """
    Checks if there are any file-level coordinates
    :param fid: a file reader (SD) object
    :return: bool - False if there are no file-level coordinates, True if there are any
    """

    coord_sets = []   # will hold datasets suspected to be coordinates

    for i in range(len(fid.datasets())):
        ds = fid.select(i)
        if bool(ds.iscoordvar()):
            coord_sets.append(ds)

    if len(coord_sets) > 0:
        return True
    else:
        return False

def get_coord_bounds(fid):
    """
    Returns the coordinate boundaries for constructing coordinates at the dataset level
    :param fid: a file reader (SD) object
    :return: a Python dictionary of String keys and numeric values
    """

    coord_attrs = {}
    # Gets our coordinate-related attributes
    for key, value in fid.attributes().items():
        if 'coordinate' in key.lower():
            coord_attrs[key] = value

    coord_bounds = {}
    # Gets our coordinate bounds
    for key in coord_attrs.keys():
        if 'north' in key.lower():
            coord_bounds['latN'] = coord_attrs[key]
        if 'south' in key.lower():
            coord_bounds['latS'] = coord_attrs[key]
        if 'east' in key.lower():
            coord_bounds['lonE'] = coord_attrs[key]
        if 'west' in key.lower():
            coord_bounds['lonW'] = coord_attrs[key]

    return coord_bounds

def get_ds_coords(fid, ds):
    """
    Returns constructed coordinates given the file reader (SD) and a dataset (SDS) object
    :param fid: an SD object
    :param ds: an SDS object
    :return: a Python dictionary of String keys and NumPy array values
    """

    bounds = get_coord_bounds(fid)

    latN = bounds['latN']
    latS = bounds['latS']
    lonE = bounds['lonE']
    lonW = bounds['lonW']

    lat_shape = ds.dimensions()['YDim']
    lon_shape = ds.dimensions()['XDim']

    if isinstance(bounds, dict):  # Have to configure dataset coords
        lat_space = (latN - latS) / lat_shape
        lon_space = (lonE - lonW) / lon_shape

        lats = np.linspace(latS, latN + lat_space, lat_shape)
        lons = np.linspace(lonW, lonE + lon_space, lon_shape)

        coords = {'lats': lats, 'lons': lons}
        return coords

    # else:   # Coords already set at file level
    # return sample_bounds

# III. Implementation - - - - - - -
def get_array(fid, var):
    """
    Returns an XArray DataArray of an HDF4 dataset given the file reader object and variable name
    :param fid: a file reader (SD) object
    :param var: a data variable String name
    :return: an XArray DataArray
    """
    ds = fid.select(var)

    coords_dict = get_ds_coords(fid, ds)
    lats = coords_dict['lats']
    lons = coords_dict['lons']

    xr_arr = xr.DataArray(restore_data(ds), coords=[lats, lons], dims=['lat', 'lon'])

    xr_arr.attrs = ds.attributes()

    dims_attrs = get_dims_attrs(ds)
    xr_arr.lat.attrs = dims_attrs['lat']
    xr_arr.lon.attrs = dims_attrs['lon']

    return xr_arr


def read_set(filename, var):
    """
    Reads a LANDSAT HDF4 filename and data variable and returns the dataset as an XArray DataArray
    :param filename: a filename String
    :param var: a data variable String name
    :return: an XArray DataArray
    """
    fid = get_fid(filename)

    if check_fid_coords(fid):  # File-level coords exist
        pass
    else:
        fid_coords = False  # File-level coords do not exist

    return get_array(fid, var)


def read_file(filename):
    """
    Reads a LANDSAT HDF4 filename and returns its data as an XArray Dataset
    :param filename: a filename String
    :return: an XArray Dataset
    """
    fid = get_fid(filename)

    if check_fid_coords(fid):  # File-level coords exist
        pass
    else:
        fid_coords = False  # File-level coords do not exist

    xr_ds = xr.Dataset()

    for name in fid.datasets().keys():
        xr_ds[name] = get_array(fid, name)

    xr_ds.attrs = fid.attributes()

    fid.end()
    return xr_ds


if __name__ == "__main__":
    # filename = str(input('Enter a LANDSAT file\'s full path: '))

    file_loc = '/Users/deonkouatchou/eviz/eviz_datasource_dev/Samples/LANDSAT/'
    file_name = 'LT50830152011198GLC00.hdf'
    file = file_loc + file_name

    print(read_set(file, 'cfmask'))
    #print(read_file(file))


