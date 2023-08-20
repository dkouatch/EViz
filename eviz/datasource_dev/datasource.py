"""


"""

from landsat_reader import LandsatReader
from omi_reader import OMIReader

import re
import logging
logging.basicConfig(level = logging.INFO)   # filename = ...

class Datasource:
    """
    Purposes:
        - Determine the source and file type of a file by reading its filename
        - Construct an XArray data structure of file data by reading its filename

    """

    def __init__(self, filename, var = None, stype = None):
        """
        Creates a Datasource object which manages file reading
        :param filename: a filename String
        :param var: a data variable String or 'None'
        """
        self.fn = filename
        self.var = var

        self.log = logging.getLogger(__name__)

        self.stype = self.get_stype()
        # self.ftype = self.get_ftype()   job passed onto reader classes for now
        self.reader = self.get_reader()
        # self.data = self.reader.data

    def __repr__(self):
        """
        Returns object data
        :return:
        """
        return f'Datasource object: {self.stype} Reader \n{repr(self.reader)}'


    def __str__(self):
        """

        :return:
        """
        return repr(self)


    def is_omi(self):
        """
        Determines if an object holds OMI info from its filename
        :return: Boolean
        """
        instr = "OM.+"
        dtype = "L[1-3]-.+"
        date = "[1-2][0-9][0-9][0-9]m[0-1][0-9][0-3][0-9].*"
        vers = "v[0-0][0-9][0-9]-" + date + "t[0-2][0-9][0-6][0-9][0-6][0-9]"
        ext = "[.]..."

        convention = "^.*" + instr + "_" + dtype + "_" + date + "_" + vers + ext
        match = re.search(convention, self.fn)

        if isinstance(match, type(None)):
            return False
        else:
            if match.group() == self.fn:
                return True
            else:
                return False

    def is_landsat(self):
        """
        Determines if an object holds Landsat info from its filename
        :return: Boolean
        """
        lxs = "L[COITEM][1-8]"
        loc = "[0-9][0-9][0-9]" + "[0-9][0-9][0-9]"
        date = "[12][0-9][0-9][0-9]" + "[0-3][0-9][0-9]"
        data = "[A-Z][A-Z][A-Z]" + "[0-9][0-9]"
        ext = "[.]..."

        convention = "^.*" + lxs + loc + date + data + ext
        match = re.search(convention, self.fn)

        if isinstance(match, type(None)):
            return False
        else:
            if match.group() == self.fn:
                return True
            else:
                return False

    def get_stype(self):
        """
        Determines and returns the source type of a Datasource object
        :return: a String or 'None'
        """
        if self.is_omi() != self.is_landsat():
            result = {True: 'OMI', False: 'Landsat'}
            return result[self.is_omi()]
        else:
            result = {True: 'Both', False: None}
            return result[self.is_omi()]

    '''
    def get_ftype(self):
        """
        Determines and returns the file type of a Datasource object
        :return:
        """
        if self.stype == 'OMI':
            if self.fn.endswith('.he4'):
                return 'HDF4'
            elif self.fn.endswith('he5'):
                return 'HDF5'
        elif self.stype == 'Landsat' or self.stype == 'MODIS':
            if self.fn.endswith('.hdf'):
                return 'HDF5'
    '''

    def get_reader(self):
        """
        Creates and returns the reader object given the source type
        :return: an OMI or Landsat Reader object or 'None'
        """
        if self.stype == 'OMI':
            self.log.info(f"INITIALIZING READER ({self.stype})")
            return OMIReader(self.fn, self.var)
        elif self.stype == 'Landsat':
            self.log.info(f"INITIALIZING READER ({self.stype})")
            return LandsatReader(self.fn, self.var)
        else:
            self.log.info("INITIALIZING READER (UNKNOWN)")
            return None


if __name__ == "__main__":
    f1_loc = '/Users/deonkouatchou/eviz/eviz_datasource_dev/Samples/OMI/'
    f1 = f1_loc + 'OMI-Aura_L3-OMTO3e_2022m0709_v003-2022m0711t031807.he5'

    f2_loc = '/Users/deonkouatchou/eviz/eviz_datasource_dev/Samples/Landsat/'
    f2 = f2_loc + 'LT50830152011214GLC00.hdf'

    f3 = f2_loc + "LT50830152011198GLC00.hdf"

    test1 = Datasource(f1, 'ColumnAmountO3')   # OMI w/ variable
    print(test1, '\n')

    test2 = Datasource(f2)   # Landsat w/o variable
    print(test2, '\n')

    test3 = Datasource(f3, ['cfmask', 'sr_band3'])   # Landsat w/ variables
    print(test3, '\n')

    test4 = Datasource(f1, ('?', '!', '@', 'SolarZenithAngle'))
    print(test4, '\n')

    # Plotting Demo
    '''
    import matplotlib.pyplot as plt
    test1.reader.data.plot()
    plt.show()
    '''
