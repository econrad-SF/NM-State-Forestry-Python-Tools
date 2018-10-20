# NM-State-Forestry-Python-Tools
Python scripts and geoprocessing tools. 

I worked as the GIS Coordinator at New Mexico State Forestry (NMSF) for 9 months prior to moving to New Mexico Department of Transportation (NMDOT). I supported both the forest resources bureau and the fire management bureau at state forestry and wrote python code to create tools that can be run by non-programmers, as well as non-GIS specialists from a GUI in ArcMap. The python code uses a number of python modules: os, re, pandas, and arcpy (ESRI). I also wrote a number of python scripts to be used by only me to help process various datasets.

Tools:
1) Convert Shapefile to WKT: User inputs shapefile into tool and code converts vertices to well-known text (WKT) and writes it to a text file. The WKT is subsequently copied and pasted into a U.S. Forest Service portal that tracks forest thinning projects.

2) E911 Analysis - Fire Mapping Tool: User inputs GPS coordinates in either decimal degrees or degrees, minutes, seconds format and python code performs spatial analysis to determine number of residences within 1 and/or 5 mile buffers. Output from python code is a map depicting fire origin, fire buffers, residences (if any), and a summary in the map title detailing how many homes could be affected. Other output includes resultant vector datasets for ArcMap and KMZ output for Google Earth. This python tool allows state forestry to quickly determine whether a new fire start qualifies for additional federal funding due to its proximity to residences.

3) Our Accomplishment Reporting System (OARS) Shapefile Developer: NMSF collects a lot of geospatial data with various kinds of GPS units. The majority of these are Garmin units which don't support data dictionaries making the data collection process messy. As a means to clean up the data, this tool takes the shapefile (DNR Garmin GPS can output shapefiles) as input, and provides the user with >15 data inputs with strict ranges and domains only allow valid inputs. This tool is now used by all of NMSF whenever they need to include shapefiles with records they need to input into separate OARS software.

4) Percent Slope Analysis Tool: User inputs a shapefile into python tool to determine how many acres occur above and below a chosen slope threshold. NMSF conducts forest thinning projects to reduce the risk of catastrophic wildfire in the wildland urban interface, as well as important watersheds. When NMSF contracts the work out to local businesses, rates are partially determined by the steepness of the terrain. This python code gives the Timber Resources Officer the flexibility to choose from several slope thresholds and the tool outputs a map depicting steep polygons in red, less steep areas in green, and labels how many acres of each for every polygon in the shapefile submitted. It also creates a graph summarizing the respecitive acreages for each unique polygon. 

Python Scripts:
1) OARS_Preparation1.py - Prior to the OARS python tool was developed, there were hundreds of shapefiles collected by NMSF with all kinds of spatial projections. This script checks loops through the shapefiles, checks their coordinate reference systems (CRS), and projects them to the desired CRS, performing a geographic transformation if necessary. It prints out messages to indicate progress, as well as, specifies which (if any) shapefiles had a CRS not accounted for by the script, and therefore were left unprojected. 
2) OARS_Preparation2.py - Merges shapefiles 
3) OARS_Preparation3_ShapefileDeveloper.py - Further OARS shapefile preparation. 
4) OARS_UniqueID.py - Example of using regular expressions 
5) IPAs.py  - Script does some simple overlay analysis to create separate Important Plant Area shapefiles by different polygons. This work was conducted for the State Botanist, Daniella Roth, whom works from New Mexico State Forestry.
6) FMS_GIS_Prep.py - Preparation of statistical fire dataset
7) FMS_GIS_Prep2.py - Preparation of statistical fire dataset
