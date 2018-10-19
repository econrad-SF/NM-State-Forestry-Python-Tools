# NM-State-Forestry-Python-Tools
Python scripts and geoprocessing tools. 

I worked as the GIS Coordinator at New Mexico State Forestry (NMSF) for 9 months prior to moving to New Mexico Department of Transportation (NMDOT). I supported both the forest resources bureau and the fire management bureau at state forestry and wrote python code to create tools that can be run by non-programmers, as well as non-GIS specialists from a GUI in ArcMap. The python tools are entirely written in ArcMap and use a number of python modules: os, re, pandas, arcpy (ESRI). I also wrote a number of python scripts to be used by only me to help process various datasets.

Tools:
1) Fire mapping automation - User inputs GPS coordinates in either decimal degrees or degrees, minutes, seconds format and python code performs spatial analysis to determine number of residences within 1 and/or 5 mile buffers. Output from python code is a map depicting fire origin, fire buffers, residences (if any), and a summary in the map title detailing how many homes could be affected. Other output includes resultant vector datasets for ArcMap and KMZ output for Google Earth. This python tool allows state forestry to quickly determine whether a new fire start qualifies for additional federal funding due to its proximity to residences.

2) Slope Analysis Tool - User inputs a shapefile into python tool to determine how many acres occur above and below a chosen slope threshold. NMSF conducts forest thinning projects to reduce the risk of catastrophic wildfire in the wildland urban interface, as well as important watersheds. When NMSF contracts the work out to local businesses, rates are partially determined by the steepness of the terrain. This python code gives the Timber Resources Officer the flexibility to choose from several slope thresholds and the tool outputs a map depicting steep polygons in red, less steep areas in green, and labels how many acres of each for every polygon in the shapefile submitted. It also creates a graph summarizing the respecitive acreages for each unique polygon. 

3) Our Accomplishment Reporting System (OARS) Tool - NMSF collects a lot of geospatial data with various kinds of GPS units. The majority of these are Garmin units which don't support data dictionaries making the data collection process messy. As a means to clean up the data, this tool takes the shapefile (DNR Garmin GPS can output shapefiles) as input, and provides the user with >15 data inputs with strict ranges and domains only allow valid inputs. This tool is now used by all of NMSF whenever they need to include shapefiles with records they need to input into separate OARS software.


Python Scripts:

