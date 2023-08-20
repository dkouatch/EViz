"""


"""

import numpy as np
import xarray as xr
# from datetime import datetime

import h5py

import logging
logging.basicConfig(level = logging.INFO)

class OMIReader:
    """
    Handles reading OMI data from HDF5 files.

    **** OMI Level 1B data files are written in HE4 format while Level 2
         and Level 3 product are in HE5 format ****
    """

    # I. Constructor
    def __init__(self, filename, var = None):
        """
        Constructs an object to generate either an XArray DataArray (if variable name given)
        or an XArray Dataset to represent OMI data from an HDF5 file.
        :param filename: a full path String of an OMI data file
        :param var: a data variable String name or tuple/list of String name(s)
        """
        self.fn = filename
        self.var_input = var
        self.var = var
        self.ftype = self.get_ftype()

        self.log = logging.getLogger(__name__)

        if isinstance(self.var, type(None)):
            self.data = self.read_file()
        else:
            self.data = self.read_set()

    def __repr__(self):
        """

        :return:
        """
        return f'Reader object: {self.ftype}; {self.var_input}; {type(self.data)} \n{self.fn}'

    # II. Accessor & Helper Functions
    def get_fid(self):
        """
        Access the file reader object for a given HDF5 file
        :return: an h5py file reader object
        """
        fid = h5py.File(self.fn, 'r')
        return fid

    def get_data_group(self, fid):
        """
        Finds and returns the contents of the file data field subgroup in dictionary format
        :param fid: a file identifier object
        :return: a Python dictionary of dataset name String keys and dataset object values
        """
        parent_contents = dict(fid['HDFEOS']['GRIDS'])  # contents of our parent group
        sub = list(parent_contents.values())[0]  # our sub-parent group object
        sub_contents = dict(sub)  # contents of our sub-parent group
        data_group = list(sub_contents.values())[0]  # our data group object

        return dict(data_group)

    # - - - - - A. Attributes
    def convert_dict_dtype(self, sample_dict):
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
                # **eval() reliability??**

            sample_dict[key] = item  # Updates any changes to the key value

        return sample_dict

    def get_fid_attrs(self, fid):
        """
        Returns the file-level attributes (in Python data types)
        :param fid: a file reader object
        :return: a Python dictionary of attributes
        """
        fid_attrs = dict(fid['HDFEOS']['ADDITIONAL']['FILE_ATTRIBUTES'].attrs)
        fid_attrs = self.convert_dict_dtype(fid_attrs)

        fid_attrs.update(self.get_plot_attrs(fid))

        return fid_attrs

    def get_plot_attrs(self, fid):
        """
        Returns the file plotting attributes (in Python data types)
        :param fid: a file reader object
        :return: a Python dictionary of attributes
        """
        parent_contents = dict(fid['HDFEOS']['GRIDS'])
        subgroup = list(parent_contents.values())[0]

        plot_attrs = dict(subgroup.attrs)
        plot_attrs = self.convert_dict_dtype(plot_attrs)

        return plot_attrs

    def get_ds_attrs(self, ds):
        """
        Returns the attributes of an HDF5 dataset (in Py
        :param ds: an HDF5 dataset object
        :return: a Python dictionary of attributes
        """
        ds_attrs = dict(ds.attrs)
        ds_attrs = self.convert_dict_dtype(ds_attrs)

        return ds_attrs

    # - - - - - B. Data Restoration
    def get_fill(self, ds_attrs):
        """
        Returns the fill value of a dataset
        :param ds_attrs: a Python dictionary of dataset attributes
        :return: an integer, float, or 'None'
        """
        for key, value in ds_attrs.items():
            if key == '_FillValue':
                return value
        return None

    def get_scale(self, ds_attrs):
        """
        Returns the scale factor of a dataset
        :param ds_attrs: a Python dictionary of dataset attributes
        :return: an integer, float, &/or 1
        """
        for key, value in ds_attrs.items():
            if key == 'ScaleFactor':
                return value
        return 1

    def get_offset(self, ds_attrs):
        """
        Returns the offset value of a dataset
        :param ds_attrs: a Python dictionary of dataset attributes
        :return: an integer, float, &/or 0
        """
        for key, value in ds_attrs.items():
            if key == 'Offset':
                return value
        return 0

    def restore_data(self, ds):
        """
        Restores the data of a given dataset object
        :param ds: an HDF5 dataset object
        :return: a NumPy array
        """
        ds_attrs = self.get_ds_attrs(ds)

        fill = self.get_fill(ds_attrs)
        scale = self.get_scale(ds_attrs)
        offset = self.get_offset(ds_attrs)

        data = ds[()]  # .astype('float')

        data = np.where(data != fill, data, np.nan)
        data *= scale
        data += offset

        data = np.expand_dims(data, axis = 0)

        return data

    # - - - - - C. Coordinates & Dimensions
    def get_time(self, fid):
        """
        Returns the time at which the data was measured/acquired
        :param fid: a file reader object
        :return: a list of a DateTime object
        """
        fid_attrs = self.get_fid_attrs(fid)

        year = month = day = None
        for key, value in fid_attrs.items():
            if 'year' in key.lower():
                year = str(value)
            elif 'month' in key.lower():
                month = str(value)
                if len(month) == 1:
                    month = '0'+month
            elif 'day' in key.lower():
                day = str(value)
                if len(day) == 1:
                    day = '0'+day

        time = year + '-' + month + '-' + day
        times = [time]
        # times = [datetime.strptime(time, '%Y %b %d')]

        return times

    def get_coords(self, fid):
        """
        Returns the coordinates of a file
        :param fid: a file reader object
        :return: a Python dictionary of String keys and NumPy array values
        """
        plot_attrs = self.get_plot_attrs(fid)

        lonW = plot_attrs['GridSpan'][0]
        lonE = plot_attrs['GridSpan'][1]
        latS = plot_attrs['GridSpan'][2]
        latN = plot_attrs['GridSpan'][3]

        lon_size = plot_attrs['NumberOfLongitudesInGrid']
        lat_size = plot_attrs['NumberOfLatitudesInGrid']

        lons = np.linspace(lonW, lonE, lon_size)
        lats = np.linspace(latS, latN, lat_size)
        times = self.get_time(fid)

        return {'times': times, 'lons': lons, 'lats': lats}

    def get_ds_dims(self, ds, coords):
        """
        Returns the dimension names of a dataset
        :param ds: a dataset object
        :param coords: a Python dictionary of file coordinates (NumPy arrays)
        :return: a Python dictionary of dimension name String keys and dimension size integer values
        """
        dims = ds.dims
        ds_dims = {'time': 1}

        for i in range(len(dims)):
            if dims[i].label == '':
                if ds.shape[i] == coords['lons'].size:
                    ds_dims['lon'] = ds.shape[i]
                elif ds.shape[i] == coords['lats'].size:
                    ds_dims['lat'] = ds.shape[i]
            else:
                if 'time' in dims[i].label.lower():
                    ds_dims['time'] = ds.shape[i]
                else:
                    ds_dims[dims[i].label] = ds.shape[i]

        return ds_dims

    def check_coords(self, dims, coords):
        """
        Rearranges order of the coordinates list to match the dimension shapes
        :param dims: a Python dictionary of dimension name String keys and dimension size integer values
        :param coords: a Python dictionary of file coordinates (NumPy arrays)
        :return: a Python dictionary of rearranged file coordinates (NumPy arrays)
        """
        if list(dims.values())[1] != list(coords.values())[1].size:
            temp = coords
            coords = {list(coords.keys())[0]: list(coords.values())[0],
                      list(coords.keys())[2]: list(coords.values())[2],
                      list(coords.keys())[1]: list(coords.values())[1]}

        return coords

    # III. Top-Level Functions
    def get_array(self, data_group, fid_coords):
        """
        Returns an XArray DataArray of an HDF5 dataset given the data field subgroup contents and
        file-level coordinates.
        :param data_group: a Python dictionary of String keys and HDF5 dataset object values
        :param fid_coords: a Python dictionary of file coordinates (NumPy arrays)
        :return: an XArray DataArray
        """
        try:
            hdf_ds = data_group[self.var]
        except Exception as e:
            if isinstance(e, KeyError):   # If variable doesn't exist
                self.log.warning(f"VARIABLE '{self.var}' DOES NOT EXIST")
            else:
                self.log.error('EXCEPTION OCCURRED', exc_info = True)
            xr_arr = None
        else:
            self.log.debug(f'CONFIGURING {self.var} ARRAY')

            data = self.restore_data(hdf_ds)
            ds_attrs = self.get_ds_attrs(hdf_ds)

            ds_dims = self.get_ds_dims(hdf_ds, fid_coords)
            ds_coords = self.check_coords(ds_dims, fid_coords)

            xr_arr = xr.DataArray(data, dims=list(ds_dims.keys()), coords=list(ds_coords.values()))
            xr_arr.attrs = ds_attrs

        return xr_arr

    def read_set(self):
        """
        Reads the OMI HDF5 File Reader object and eturns the dataset(s) as an XArray DataArray/Dataset
        :return: an XArray DataArray or Dataset
        """
        fid = self.get_fid()
        self.log.info('READING FILE')

        data_group = self.get_data_group(fid)
        fid_coords = self.get_coords(fid)

        if isinstance(self.var_input, str):
            xr_arr = self.get_array(data_group, fid_coords)
            self.log.info('DATA ARRAY CREATED')

            try:
                xr_arr.name = self.var_input
            except AttributeError:
                self.log.warning('EMPTY DATA ARRAY')

            self.log.info('CLOSING FILE')
            fid.close()

            return xr_arr

        elif isinstance(self.var_input, tuple) or isinstance(self.var_input, list):
            if len(self.var_input) == 1:
                self.var = self.var_input[0]
                xr_arr = self.get_array(data_group, fid_coords)
                self.log.info('DATA ARRAY CREATED')

                try:
                    xr_arr.name = self.var_input[0]
                except AttributeError:
                    self.log.warning('EMPTY DATA ARRAY')

                self.log.info('CLOSING FILE')
                fid.close()

                return xr_arr

            else:
                xr_ds = xr.Dataset()

                fid_attrs = self.get_fid_attrs(fid)

                for var in self.var_input:
                    if var in data_group.keys():
                        self.var = var
                        xr_ds[var] = self.get_array(data_group, fid_coords)
                    else:
                        self.log.warning(f"VARIABLE '{var}' DOES NOT EXIST")

                xr_ds.attrs = fid_attrs
                self.log.info('DATASET CREATED')

                self.log.info('CLOSING FILE')
                fid.close()

                if '*empty*' in repr(xr_ds.data_vars):  # If the dataset is empty
                    self.log.warning('EMPTY DATASET')
                    return None
                else:
                    return xr_ds
        else:
            return None

    def read_file(self):
        """
        Reads an OMI HDF5 filename and returns its data as an XArray Dataset
        :return: an XArray Dataset
        """
        xr_ds = xr.Dataset()

        fid = self.get_fid()
        self.log.info('READING FILE')

        data_group = self.get_data_group(fid)
        fid_attrs = self.get_fid_attrs(fid)
        fid_coords = self.get_coords(fid)

        for var in data_group.keys():
            self.var = var
            xr_ds[var] = self.get_array(data_group, fid_coords)

        xr_ds.attrs = fid_attrs
        self.log.info('DATASET CREATED')

        self.log.info('CLOSING FILE')
        fid.close()

        if '*empty*' in repr(xr_ds.data_vars):   # If the dataset is empty
            self.log.warning('EMPTY DATASET')
            return None
        else:
            return xr_ds

    # IV. Future OOP Things
    def get_ftype(self):
        """
        Determines and returns the file type of the OMI Reader object
        :return: String of file type or 'None'
        """
        if self.fn.endswith('.he5'):
            return 'HDF5'
        elif self.fn.endswith('.he4'):
            return 'HDF4'
        else:
            return None


if __name__ == "__main__":
    f_loc = '/Users/deonkouatchou/eviz/eviz_datasource_dev/Samples/OMI/'
    f = f_loc + 'OMI-Aura_L3-OMTO3e_2022m0709_v003-2022m0711t031807.he5'

    obj1 = OMIReader(f)
    #print(obj1, '\n')

    obj2 = OMIReader(f, 'ColumnAmountO3')
    #print(obj2.data, '\n')

    obj3 = OMIReader(f, ['SolarZenithAngle'])
    #print(obj3, '\n')

    obj4 = OMIReader(f, ('RadiativeCloudFraction', 'ViewingZenithAngle'))
    #print(obj4, '\n')

    obj5 = OMIReader(f, '?')
    #print(obj5, '\n')

    obj6 = OMIReader(f, var = ['!', '?'])
    #print(obj6, '\n')
