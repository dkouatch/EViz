"""
Author:
Date: 25-07-2022

The purpose of this file is to define the functions necessary to read a file of a collection of data
from the Ozone Monitoring Instrument (OMI) and convert it into an XArray Dataset object.

File Collection: OMI Satellite
File Format: HDF5
File-Reading Package: H5py
File Naming Conventions:
    <Instrument ID>_<Data Type>_<Data ID>_<Version Info>.<Suffix>

    • Instrument ID: ID for instrument and spacecraft
        ex. 'OMI-Aura' -> OMI on the Aura spacecraft
    • Data Type: level and product indicators
        ex. 'L3-OMNO2d' -> OMI Level 3 NO2 data product
    • Data ID:
        Format:
        <date>
            <yyyy>m<mmdd>t<hhmmss>
    • Version:
        Format:
        v<version>-<production date and time>
            version -> <nnn>
            date-time -> <yyyy>m<mmdd>t<hhmmss>
    • Suffix
        ex. 'he5'

    ex. OMI-Aura_L3-OMTO3e_2022m0709_v003-2022m0711t031807.he5
        • Instrument ID: OMI on the Aura spacecraft
        • Data Type: OMI Level 3
        • Data ID: July 9, 2022
        • Version:
            Version No. 003
            Production Date & Time - July 11, 2022 at 03:18:07 (UTC)
        • Suffix: he5
"""

# I. IMPORT STATEMENTS - - - - - - -
import numpy as np
import xarray as xr
import h5py

# II. ACCESSOR & HELPER METHODS - - - - - - -

def get_fid(filename):
    """
    Access the file reader object for a given HDF5 file
    :param filename: a String
    :return: an h5py file reader object
    """
    fid = h5py.File(filename, 'r')
    return fid


def get_data_group(fid):
    """
    Finds and returns the contents of the file data field subgroup in dictionary format
    :param fid: a file identifier object
    :return: a Python dictionary of dataset name String keys and dataset object values
    """
    parent_contents = dict(fid['HDFEOS']['GRIDS'])  # contents of our parent group
    subparent = list(parent_contents.values())[0]  # our subparent group object
    subparent_contents = dict(subparent)  # contents of our subparent group
    data_group = list(subparent_contents.values())[0]  # our data group object

    return dict(data_group)

#     #     #
def convert_dict_dtype(sample_dict):
    """
    Converts a dictionary of attributes from NumPy data types to general Python data types
    :param sample_dict: a Python dictionary of attributes
    :return: a Python dictionary of attributes
    """
    for key, item in sample_dict.items():
        if isinstance(item, np.ndarray):  # Converts np arrays to a list to, if applicable, an int or float
            item = list(item)

            if len(item) == 1:
                item = item[0]
        elif isinstance(item, np.bytes_):  # Converts np bytes to an np string to a Python string
            item = str(item.astype('str'))

            if item[0] == '(' or item[0] == '{':  # Converts to tuple or dict if applicable
                item = eval(item)
            # **eval() relaiability??**

        sample_dict[key] = item  # Updates any changes to the key value

    return sample_dict


def get_fid_attrs(fid):
    """
    Returns the file-level attributes (in Python data types)
    :param fid: a file reader object
    :return: a Python dictionary of attributes
    """
    fid_attrs = dict(fid['HDFEOS']['ADDITIONAL']['FILE_ATTRIBUTES'].attrs)
    fid_attrs = convert_dict_dtype(fid_attrs)

    fid_attrs.update(get_plot_attrs(fid))

    return fid_attrs


def get_plot_attrs(fid):
    """
    Returns the file plotting attributes (in Python data types)
    :param fid: a file reader object
    :return: a Python dictionary of attributes
    """
    parent_contents = dict(fid['HDFEOS']['GRIDS'])
    subgroup = list(parent_contents.values())[0]

    plot_attrs = dict(subgroup.attrs)
    plot_attrs = convert_dict_dtype(plot_attrs)

    return plot_attrs


def get_ds_attrs(ds):
    """
    Returns the attributes of an HDF5 dataset (in Py
    :param ds: an HDF5 dataset object
    :return: a Python dictionary of attributes
    """
    ds_attrs = dict(ds.attrs)
    ds_attrs = convert_dict_dtype(ds_attrs)

    return ds_attrs

#     #     #
def get_fill(ds_attrs):
    """
    Returns the fill value of a dataset
    :param ds_attrs: a Python dictionary of dataset attributes
    :return: an integer, float, or 'None'
    """
    for key, value in ds_attrs.items():
        if key == '_FillValue':
            return value
    return None


def get_scale(ds_attrs):
    """
    Returns the scale factor of a dataset
    :param ds_attrs: a Python dictionary of dataset attributes
    :return: an integer, float, &/or 1
    """
    for key, value in ds_attrs.items():
        if key == 'ScaleFactor':
            return value
    return 1


def get_offset(ds_attrs):
    """
    Returns the offset value of a dataset
    :param ds_attrs: a Python dictionary of dataset attributes
    :return: an integer, float, &/or 0
    """
    for key, value in ds_attrs.items():
        if key == 'Offset':
            return value
    return 0


def restore_data(ds):
    """
    Restores the data of a given dataset object
    :param ds: an HDF5 dataset object
    :return: a NumPy array
    """
    ds_attrs = get_ds_attrs(ds)

    fill = get_fill(ds_attrs)
    scale = get_scale(ds_attrs)
    offset = get_offset(ds_attrs)

    data = ds[()]  # .astype('float')

    data = np.where(data != fill, data, np.nan)
    data *= scale
    data += offset

    return data

#     #     #
def get_coords(fid):
    """
    Returns the coordinates of a file
    :param fid: a file reader object
    :return: a Python dictionary of String keys and NumPy array values
    """
    plot_attrs = get_plot_attrs(fid)

    lonW = plot_attrs['GridSpan'][0]
    lonE = plot_attrs['GridSpan'][1]
    latS = plot_attrs['GridSpan'][2]
    latN = plot_attrs['GridSpan'][3]

    lon_size = plot_attrs['NumberOfLongitudesInGrid']
    lat_size = plot_attrs['NumberOfLatitudesInGrid']

    lons = np.linspace(lonW, lonE, lon_size)
    lats = np.linspace(latS, latN, lat_size)

    return {'lons': lons, 'lats': lats}


def get_ds_dims(ds, coords):
    """
    Returns the dimension names of a dataset
    :param ds: a dataset object
    :param coords: a Python dictionary of file coordinates (NumPy arrays)
    :return: a Python dictionary of dimension name String keys and dimension size integer values
    """
    dims = ds.dims
    ds_dims = {}

    for i in range(len(dims)):
        if dims[i].label == '':
            if ds.shape[i] == coords['lons'].size:
                ds_dims['lon'] = ds.shape[i]
            elif ds.shape[i] == coords['lats'].size:
                ds_dims['lat'] = ds.shape[i]
        else:
            ds_dims[dims[i].label] = ds.shape[i]

    return ds_dims


def check_coords(dims, coords):
    """
    Rearranges order of the coordinates list to match the dimension shapes
    :param dims: a Python dictionary of dimension name String keys and dimension size integer values
    :param coords: a Python dictionary of file coordinates (NumPy arrays)
    :return: a Python dictionary of rearranged file coordinates (NumPy arrays)
    """
    if list(dims.values())[0] != list(coords.values())[0].size:
        temp = coords
        coords = {list(coords.keys())[1]: list(coords.values())[1],
                  list(coords.keys())[0]: list(coords.values())[0]}
    return coords


# III. IMPLEMENTATION - - - - - - -
def get_array(data_group, fid_coords, var):
    """
    Returns an XArray DataArray of an HDF5 dataset given the data field subgroup contents,
    file-level coordinates, and data variable name.
    :param data_group: a Python dictionary of String keys and HDF5 dataset object values
    :param fid_coords: a Python dictionary of file coordinates (NumPy arrays)
    :param var: a data variable String name
    :return: an XArray DataArray
    """
    hdf_ds = data_group[var]

    data = restore_data(hdf_ds)
    ds_attrs = get_ds_attrs(hdf_ds)

    ds_dims = get_ds_dims(hdf_ds, fid_coords)
    ds_coords = check_coords(ds_dims, fid_coords)

    xr_arr = xr.DataArray(data, dims=list(ds_dims.keys()), coords=list(ds_coords.values()))
    xr_arr.attrs = ds_attrs

    return xr_arr


def read_set(filename, var):
    """
    Reads an OMI HDF5 filename and data variable and returns the dataset as an XArray DataArray
    :param filename: a filename String
    :param var: a data variable String name
    :return: an XArray DataArray
    """
    fid = get_fid(filename)

    data_group = get_data_group(fid)
    fid_coords = get_coords(fid)

    return get_array(data_group, fid_coords, var)


def read_file(filename):
    """
    Reads an OMI HDF5 filename and returns its data as an XArray Dataset
    :param filename: a filename String
    :return: an XArray Dataset
    """
    xr_ds = xr.Dataset()

    fid = get_fid(filename)

    data_group = get_data_group(fid)
    fid_attrs = get_fid_attrs(fid)
    fid_coords = get_coords(fid)

    for name in data_group.keys():
        xr_ds[name] = get_array(data_group, fid_coords, name)

    xr_ds.attrs = fid_attrs

    fid.close()
    return xr_ds


if __name__ == "__main__":
    #filename = str(input('Enter an OMI file\'s full path: '))

    file_loc = '/Users/deonkouatchou/eviz/eviz_datasource_dev/Samples/OMI/'
    file_name = 'OMI-Aura_L3-OMTO3e_2022m0709_v003-2022m0711t031807.he5'
    file = file_loc + file_name

    print(read_set(file, 'ColumnAmountO3'))
    print(read_file(file))
