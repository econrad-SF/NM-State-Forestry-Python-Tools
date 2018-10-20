#-------------------------------------------------------------------------------
# Name:    OARS Prep Tool #1
# Purpose: This tool checks the coordinate reference system of each shapefile in
#          the folder and reprojects to NAD83 UTM Zone 13N if necessary. Once all
#          shapefiles are in the correct CRS, they are merged together and
#          unneccessary attributes are deleted. The projected shapefiles are renamed
#          with "_proj" at the end. This script works on shapefiles in the Raw Data
#          folder (e.g. OARS S_FY17). OARS Script 2 picks off from reading files from
#          the same folder.
#
# Author:      Ed Conrad
# Created:     Feb. 16, 2017
# Copyright:   (c) Ed Conrad 2017
#-------------------------------------------------------------------------------# ------------------------------ Instructions for Use -------------------# Need to Change 1 thing to run
import arcpy, os, re
from arcpy import env
scriptpath = os.getcwd()
year = "2018"                                                                   # <-------------------------------------------------------------------------------- (1) Change Year
folder = "OARS Raw Data\OARS S_FY{0}".format(year[2:])
OARSdata = os.path.join(scriptpath, folder)
tempData = os.path.join(scriptpath, "OARS Temp")
folder2 = "OARS Null or Wrong Geometry\State_FY\S_FY{0}".format(year[2:])
wrongGeometry = os.path.join(scriptpath, folder2)
env.workspace = OARSdata
env.overwriteOutput = False

# Remove non-shapefiles from OARS folder.
for (path, dirs, files) in os.walk(OARSdata):
    for f in files:
        filename = f
        if filename[-4:] in (".pdf", ".ocx", ".mxd", ".zip"):
            print("{0} was deleted from the OARS folder.".format(f))
            os.remove(os.path.join(OARSdata, f))

# Loop through all files, check syntax. If illegal characters exist, rename file without the invalid characters (includes periods)
for (path, dirs, files) in os.walk(OARSdata):
    for f in files:
        filename = f
        pattern = re.compile('[^a-zA-Z_0-9-]+')
        if pattern.findall(filename):
            newName = pattern.sub("", filename)
            formatName = "{0}.{1}".format(newName[:-3], newName[-3:])
            os.rename(os.path.join(OARSdata, f), os.path.join(OARSdata, formatName))
        else: pass

# Move shapefiles that aren't polygons to "OARS Null or Wrong Geometry" folder
fcList = arcpy.ListFeatureClasses()
count = 0
for fc in fcList:
    geometry = arcpy.Describe(fc).shapeType
    if geometry == "Polygon":
        pass
    else:
        name = fc
        name = name[:-4]
        for (path, dirs, files) in os.walk(OARSdata):
            for f in files:
                filename = f
                filename = filename[:-4]
                if filename == name:
                    os.rename(os.path.join(OARSdata, f), os.path.join(wrongGeometry, f))
                    count +=1
                    print("{0} files were moved to the 'Wrong Geometry' folder.".format(count))


# Add Field called, "Orig_Name", to each Shapefile and populate it with original name
fcList = arcpy.ListFeatureClasses()
for fc in fcList:
    filename = fc
    arcpy.AddField_management(fc, "Orig_Name", "TEXT", "", "", 250)
    arcpy.CalculateField_management(fc, "Orig_Name", '"' + str(filename) + '"', "PYTHON")


# Loop through shapefiles with Polygon geometry, check CRS, and project to NAD83 UTM Zone 13N with appropriate geographic transformation if necessary.
fcList = arcpy.ListFeatureClasses()                                             # Refresh shapefile list.
sr = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")
for fc in fcList:
    baseName = arcpy.Describe(fc).baseName
    crs = arcpy.Describe(fc).spatialReference
    crs_string = crs.exporttostring()
    NAD83_HARN = re.compile("D_North_American_1983_HARN")                       # Check shapefile Datum in order to specify correct geographic transformation if necessary.
    WGS_1984 = re.compile("D_WGS_1984")
    NAD83 = re.compile("D_North_American_1983")
    NAD27 = re.compile("D_North_American_1927")
    if NAD83_HARN.findall(crs_string):
        print("File {0}, has incorrect datum: 'D_North_American_1983_HARN' and incorrect projection {1}. Reprojecting...".format(baseName, crs.name))
        arcpy.Project_management(fc, baseName + "_proj.shp", sr, "NAD_1983_To_HARN_New_Mexico")
        arcpy.Delete_management(fc)
    elif WGS_1984.findall(crs_string):
        print("File {0}, has incorrect datum: 'D_WGS_1984' and incorrect projection {1}. Reprojecting...".format(baseName, crs.name))
        arcpy.Project_management(fc, baseName + "_proj.shp", sr, "WGS_1984_(ITRF00)_To_NAD_1983")
        arcpy.Delete_management(fc)
    elif NAD27.findall(crs_string):
        print("File {0}, has incorrect datum: 'D_North_American_1927' and incorrect projection {1}. Reprojecting...".format(baseName, crs.name))
        arcpy.Project_management(fc, baseName + "_proj.shp", sr, "NAD_1927_To_NAD_1983_NADCON")
        arcpy.Delete_management(fc)
    elif NAD83.findall(crs_string) and crs.name != "NAD_1983_UTM_Zone_13N":
        print("File {0} has correct datum: 'D_North_American_1983', but incorrect projection ({1}). Reprojecting...".format(baseName, crs.name))
        arcpy.Project_management(fc, baseName + "_proj.shp", sr)
        arcpy.Delete_management(fc)
    elif crs.name == "Unknown":
        print("File {0}, has 'Unknown' spatial reference. It will be defined as 'NAD 1983 UTM Zone 13N'".format(baseName))
        arcpy.DefineProjection_management(fc, sr)
    elif NAD83.findall(crs_string) and crs.name == "NAD_1983_UTM_Zone_13N":     # If true, shapefile already has correct datum and projection.
        pass
    else:
        count2 = 0
        count2 += 1
        print("({0}) {1} has projection {2}. It is currently unaccounted for in this script.........................................................!".format(count2, baseName, crs.name))


# Check that all shapfiles of Polygon Geometry have NAD83 UTM Zone 13N projection. If so, proceed to script 2.
if 'count2' in locals():
    print("Merge won't run until shapefiles with incorrect projection are fixed.")
else:
    print("Shapefiles have been successfully processed by 'OARS_Preparation1.py' script. You can now use 'OARS_Preparation2.py' script............. :-) ")