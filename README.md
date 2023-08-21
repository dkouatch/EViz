# EViz: Easy Visualization of Earth-systems Models
### About
This repository showcases my work during the summer of 2022 on EViz during my internship with Science Systems and Applications, Inc. as a Software Developer Engineer. The three main portions of the repository are my [presentation](./EViz_Prez.pdf), the [code](./eviz/) I developed, and the Jupyter Notebook tutorials I created.

I was part of the NASA's [Advanced Software Technology Group](https://astg.pages.smce.nasa.gov/website/) (ASTG) and the [NASA Center for Climate Solutions](https://www.nccs.nasa.gov) (NCCS) at NASA Goddard Space Flight Center.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;![ASTG Logo](./Images/ASTG_logo_dark.png)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;![NCCS Logo](./Images/NCCS_logo.jpeg)

For more information about EViz, visit [ASTG's website](https://astg.pages.smce.nasa.gov/website/research/#easy%20visualization%20of%20earth%20system%20models) and [EViz's documentation website](https://astg.pages.smce.nasa.gov/visualization/eviz/index.html).

---
### Project Objective
EViz consists of two tools:
* eViz: A command-line input plotting tool configurable by YAML files
* iViz: An interactive visualization tool that gives clients greater freedom to explore data

The objective of my internship was to expand EViz (iViz in particular), to read satellite data as at the time, it had only been developed to handle Earth-systems model data.

![Slide from EViz_Prez.pdf](./Images/EViz_ProjectScope.png)

iViz had already been developed to handle the visualization process past the point of transforming data files into a Python `XArray` object. Thus, my objective was to process satellite data into an `XArray` object to then pass along to the main `iviz.py` file. This was accomplished by the creation of a `Datasource` class and several other files that would handle all of this.

---
### Project Details
Severall satellites process information in databases in Hierarchical Data Format (HDF) and while the exact organization of data may vary, they can be extracted similarly using Python.

Two satellites of focus for this project were Landsat 5 and the Ozone Monitoring Instrument (OMI). The file format Landsat 5 is HDF Version 4 (HDF4) and the Python module `PyHDF` is what I used to read files. The OMI uses HDF Version 5 (HDF5) and the Python module `H5py` is what I used.

There were three stages of refining this process:
1. Creating Jupyter notebooks to explore reading files
   * See the notebook for reading Landsat 5 data [here](./eviz/JupyterNotebooks/pyhdf_LANDSAT_demo.ipynb)
   * See the notebook for reading OMI data [here](./eviz/JupyterNotebooks/h5py_OMI_demo.ipynb)
2. Writing preliminary Python files that contain functions that perform the data transformation into `XArray` datatypes based on Jupyter notebook findings
   * See the preliminary file for Landsat 5: [read_LANDSAT.py](./eviz/datasource_dev/read_LANDSAT.py)
   * See the preliminary file for OMI: [read_OMI.py](./eviz/datasource_dev/read_OMI.py)
3. Final implementation of Python files to be imported and used in the `Datasource` class in `datasource.py`
   * See the final implementation for reading Landsat 5 data: [landsat_reader.py](./eviz/datasource_dev/landsat_reader.py)
   * See the final implementation for reading OMI data: [omi_reader.py](./eviz/datasource_dev/omi_reader.py)
  
The `Datasource` class is set up to be responsible for reading satellite data and other models who store data in HDF.
To explore its functionality and integration with iViz, I wrote a Jupyter notebook which can be examined [here](./eviz/JupyterNotebooks/datasource_demo.ipynb). 
The file itself containing the class is [datasource.py](./eviz/datasource_dev/datasource.py).
