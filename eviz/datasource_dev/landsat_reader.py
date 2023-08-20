"""


"""

import numpy as np
import xarray as xr
# from datetime import datetime

import pyhdf.error
from pyhdf.SD import SD, SDC

import logging
logging.basicConfig(level = logging.INFO)

class LandsatReader:
    """
    Handles reading Landsat data from HDF4 files.
    """

    # I. Constructor
    def __init__(self, filename, var = None):
        """
        Constructs an object to generate either an XArray DataArray (if variable name given)
        or an XArray Dataset to represent Landsat data from an HDF4 file.
        :param filename: a full path String of a Landsat data file
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

    # II. Accessor & Helper Methods
    def get_fid(self):
        """
        Accesses the file reader object for a file
        :return: a file reader (SD) object
        """
        fid = SD(self.fn, SDC.READ)
        return fid

    # - - - - - A. Data Restoration
    def get_fill(self, ds):
        """
        Returns the fill value of a given dataset (SDS) object
        :param ds: an SDS object
        :return: float, int, or 'None'
        """
        for key, value in ds.attributes().items():
            if key == '_FillValue':
                return value
        return None

    def get_scale(self, ds):
        """
        Returns the scale factor of a given dataset (SDS) object
        :param ds: an SDS object
        :return: float, int, or 1
        """
        for key, value in ds.attributes().items():
            if key == 'scale_factor':
                return value
        return 1

    def get_offset(self, ds):
        """
        Returns the offset value of a given dataset (SDS) object
        :param ds: an SDS object
        :return: float, int, or 0
        """
        for key, value in ds.attributes().items():
            if key == 'add_offset':
                return value
        return 0

    def restore_data(self, ds):
        """
        Restores the data o a given dataset (SDS) object
        :param ds: an SDS object
        :return: a NumPy array
        """
        fill = self.get_fill(ds)
        scale = self.get_scale(ds)
        offset = self.get_offset(ds)

        data = ds.get()  # .astype('float')

        data = np.where(data != fill, data, np.nan)  # fill
        data *= scale  # scale
        data += offset  # offset

        data = np.expand_dims(data, axis = 0)

        return data

    # - - - - - B. Dimensions
    def get_dims(self, ds):
        """
        Returns the dimension (SDim) objects of a given dataset (SDS) object
        :param ds: an SDS object
        :return: a Python list of SDim objects
        """
        dims = []  # Will actually hold dimension objects

        for i in range(len(ds.dimensions())):
            dims.append(ds.dim(i))

        return dims

    def get_dim_attrs(self, dim):
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

    def get_dims_attrs(self, ds):
        """
        Returns the dimension attributes for a given dataset (SDS) object
        :param ds: an SDS object
        :return: a Python dictionary of String keys and dictionary values
        """
        dims_attrs = {}
        dims = self.get_dims(ds)

        for dim in dims:
            if dim.info()[0] == 'YDim':
                dims_attrs['lat'] = self.get_dim_attrs(dim)
            elif dim.info()[0] == 'XDim':
                dims_attrs['lon'] = self.get_dim_attrs(dim)

        return dims_attrs

    # - - - - - C. Coordinates
    def check_fid_coords(self, fid):
        """
        Checks if there are any file-level coordinates
        :param fid: a file reader (SD) object
        :return: bool - False if there are no file-level coordinates, True if there are any
        """
        coord_sets = []  # will hold datasets suspected to be coordinates

        for i in range(len(fid.datasets())):
            ds = fid.select(i)
            if bool(ds.iscoordvar()):
                coord_sets.append(ds)

        if len(coord_sets) > 0:
            return True
        else:
            return False

    def get_coord_bounds(self, fid):
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

    def get_ds_coords(self, fid, ds):
        """
        Returns constructed coordinates given the file reader (SD) and a dataset (SDS) object
        :param fid: an SD object
        :param ds: an SDS object
        :return: a Python dictionary of String keys and NumPy array values
        """
        bounds = self.get_coord_bounds(fid)

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
            times = [self.get_time(fid)]

            coords = {'times': times, 'lats': lats, 'lons': lons}
            return coords

        # else:   # Coords already set at file level
        # return sample_bounds

    def get_time(self, fid):
        """
        Returns the time(s) at which the data was measured/acquired
        :param fid: an SD object
        :return: a DateTime object
        """
        time = fid.attributes()['AcquisitionDate']
        return time

    # III. Top-Level Methods
    def get_array(self, fid):
        """
        Returns an XArray DataArray of an HDF4 dataset given the file and Landsat reader objects
        :param fid: a file reader (SD) object
        :return: an XArray DataArray
        """
        try:
            ds = fid.select(self.var)
        except Exception as e:
            if isinstance(e, pyhdf.error.HDF4Error):
                self.log.warning(f"VARIABLE '{self.var}' DOES NOT EXIST")
            else:
                self.log.error('EXCEPTION OCCURRED', exc_info = True)
            xr_arr = None
        else:
            self.log.debug(f'CONFIGURING {self.var} ARRAY')

            coords_dict = self.get_ds_coords(fid, ds)
            lats = coords_dict['lats']
            lons = coords_dict['lons']
            times = coords_dict['times']

            xr_arr = xr.DataArray(self.restore_data(ds), coords=[times, lats, lons], dims=['time', 'lat', 'lon'])

            xr_arr.attrs = ds.attributes()

            dims_attrs = self.get_dims_attrs(ds)
            xr_arr.lat.attrs = dims_attrs['lat']
            xr_arr.lon.attrs = dims_attrs['lon']

        return xr_arr

    def read_set(self):
        """
        Reads a LANDSAT HDF4 Reader object and returns the dataset(s) as an XArray DataArray/Dataset
        :return: an XArray DataArray or Dataset
        """
        fid = self.get_fid()
        self.log.info('READING FILE')

        if self.check_fid_coords(fid):  # File-level coords exist
            pass
        else:
            fid_coords = False  # File-level coords do not exist

        if isinstance(self.var_input, str):
            xr_arr = self.get_array(fid)
            self.log.info('DATA ARRAY CREATED')

            try:
                xr_arr.name = self.var_input
            except AttributeError:
                self.log.warning('EMPTY DATA ARRAY')

            self.log.info('CLOSING FILE')
            fid.end()

            return xr_arr

        elif isinstance(self.var_input, tuple) or isinstance(self.var_input, list):
            if len(self.var_input) == 1:
                self.var = self.var_input[0]
                xr_arr = self.get_array(fid)
                self.log.info('DATA ARRAY CREATED')

                try:
                    xr_arr.name = self.var_input[0]
                except AttributeError:
                    self.log.warning('EMPTY DATA ARRAY')

                self.log.info('CLOSING FILE')
                fid.end()

                return xr_arr
            else:
                xr_ds = xr.Dataset()

                for var in self.var_input:
                    if var in fid.datasets().keys():
                        self.var = var
                        xr_ds[var] = self.get_array(fid)
                    else:
                        self.log.warning(f"VARIABLE '{var}' DOES NOT EXIST")

                xr_ds.attrs = fid.attributes()
                self.log.info('DATASET CREATED')

                self.log.info('CLOSING FILE')
                fid.end()

                if '*empty*' in repr(xr_ds.data_vars):  # If the dataset is empty
                    self.log.warning('EMPTY DATASET')
                    return None
                else:
                    return xr_ds
        else:
            return None

    def read_file(self):
        """
        Reads a LANDSAT HDF4 Reader object and returns its data as an XArray Dataset
        :return: an XArray Dataset
        """
        fid = self.get_fid()
        self.log.info('READING FILE')

        if self.check_fid_coords(fid):  # File-level coords exist
            pass
        else:
            fid_coords = False  # File-level coords do not exist

        xr_ds = xr.Dataset()

        for var in fid.datasets().keys():
            self.var = var
            xr_ds[var] = self.get_array(fid)

        xr_ds.attrs = fid.attributes()
        self.log.info('DATASET CREATED')

        fid.end()
        self.log.info('CLOSING FILE')

        if '*empty*' in repr(xr_ds.data_vars):  # If the dataset is empty
            self.log.warning('EMPTY DATASET')
            return None
        else:
            return xr_ds

    # IV. Future OOP Things
    def get_ftype(self):
        """
        Determines and returns the file type of the Landsat Reader object
        :return: String of file type or 'None'
        """
        if self.fn.endswith('hdf'):
            return 'HDF4'
        else:
            return None


if __name__ == "__main__":
    f_loc = '/Users/deonkouatchou/eviz/eviz_datasource_dev/Samples/Landsat/'
    f1 = f_loc + 'LT50830152011198GLC00.hdf'
    f2 = f_loc + 'LT50830152011214GLC00.hdf'

    obj1 = LandsatReader(f1)
    #print('\n', obj1)

    obj2 = LandsatReader(f2, 'cfmask')
    #print('\n', obj2)

    obj3 = LandsatReader(f1, ['toa_band6'])
    #print('\n', obj3)

    obj4 = LandsatReader(f2, ('toa_band6_qa', 'sr_band1', 'sr_band4'))
    #print('\n', obj4)

    obj5 = LandsatReader(f1, '?')
    #print('\n', obj5)

    obj6 = LandsatReader(f1, ['!', '?'])
    #print('\n', obj6)
