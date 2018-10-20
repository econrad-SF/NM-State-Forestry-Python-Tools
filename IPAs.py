#-------------------------------------------------------------------------------
# Name:
# Purpose:
"""This script prepared Daniela's IPAs. Shapefile outputs are IPAs by county,
IPA_Plants by county and each IPA as its own shapefile."""
# Author:      Ed Conrad
# Created:     05/12/2017
# Copyright:   (c) Ed Conrad 2017
# Licence:     ArcGIS 10.4
#-------------------------------------------------------------------------------
import arcpy, os, re
from arcpy import env
scriptpath = os.getcwd()
env.workspace = scriptpath
env.overwriteOutput = True

# Reference Files
IPA = "C:/Documents/EConrad/Work for Others/Daniela Roth/IPAs/IPA_Final.shp"
IPA_plants = "C:/Documents/EConrad/Work for Others/Daniela Roth/IPAs/IPA_Plants_Final.shp"
county = "C:/Documents/EConrad/Data/NMSF/NMSF.gdb/Boundaries/County"
district = "C:/Documents/EConrad/Data/NMSF/NMSF.gdb/Boundaries/NMSF_Districts"

# Create County list based on "NAME10" attribute
counties = ['Bernalillo', 'Catron', 'Chaves', 'Cibola', 'Colfax', 'Curry', 'De Baca', 'Dona Ana', 'Eddy', 'Grant', 'Guadalupe', 'Harding', 'Hidalgo', 'Lea', 'Lincoln', 'Los Alamos', 'Luna', 'McKinley', 'Otero', 'Quay', 'Rio Arriba', 'Roosevelt', 'San Juan', 'San Miguel', 'Sandoval', 'Santa Fe', 'Sierra', 'Socorro', 'Taos', 'Torrance', 'Union', 'Valencia']
districts = ['Bernalillo', 'Capitan', 'Chama', 'Cimarron', 'Las Vegas', 'Socorro']

""" Create Shapfiles by County
"""
# 1)  Make IPA County Shapefiles if a county has one or more intersecting IPA
arcpy.MakeFeatureLayer_management(IPA, "IPA_lyr")
for c in counties:
    arcpy.MakeFeatureLayer_management(county, "{0}_lyr".format(c), '"NAME10" = ' + "'{0}'".format(c))
    arcpy.SelectLayerByLocation_management("IPA_lyr", "INTERSECT", "{0}_lyr".format(c))
    arcpy.CopyFeatures_management("IPA_lyr", os.path.join(scriptpath, "By County\IPAs\IPA_{0}_County.shp".format(c)))

# 2) Make IPA Plants County Shapefiles if a county has one or more intersecting hexagons
arcpy.MakeFeatureLayer_management(IPA_plants, "IPA_plants_lyr")
for c in counties:
    arcpy.MakeFeatureLayer_management(county, "{0}_lyr".format(c), '"NAME10" = ' + "'{0}'".format(c))
    arcpy.SelectLayerByLocation_management("IPA_plants_lyr", "INTERSECT", "{0}_lyr".format(c))
    arcpy.CopyFeatures_management("IPA_plants_lyr", os.path.join(scriptpath, "By County\IPA Plants\IPA_Plants_{0}_County.shp".format(c)))


""" Create Shapefiles by District
"""

arcpy.MakeFeatureLayer_management(IPA, "IPA_lyr")
for d in districts:
    arcpy.MakeFeatureLayer_management(district, "{0}_lyr".format(d), '"NAME" = ' + "'{0}'".format(d))
    arcpy.SelectLayerByLocation_management("IPA_lyr", "INTERSECT", "{0}_lyr".format(d))
    arcpy.CopyFeatures_management("IPA_lyr", os.path.join(scriptpath, "By District\IPAs\IPA_{0}_District.shp".format(d)))

arcpy.MakeFeatureLayer_management(IPA_plants, "IPA_plants_lyr")
for d in districts:
    arcpy.MakeFeatureLayer_management(district, "{0}_lyr".format(d), '"NAME" = ' + "'{0}'".format(d))
    arcpy.SelectLayerByLocation_management("IPA_plants_lyr", "INTERSECT", "{0}_lyr".format(d))
    arcpy.CopyFeatures_management("IPA_plants_lyr", os.path.join(scriptpath, "By District\IPA Plants\IPA_Plants_{0}_District.shp".format(d)))

""" Create Shapefiles by IPA
"""
# 3) Make each IPA its own shapefile:
# Use Regex that removes invalid charcaters for naming shapefiles and use FID to select each record then save it as a shapefile with new name.
patternFinder = re.compile('[\W]+')
arcpy.MakeFeatureLayer_management(IPA, "IPA_lyr")
with arcpy.da.SearchCursor(IPA, ["FID", "Site_Name"]) as cursor:
    for row in cursor:
        newName = patternFinder.sub("", row[1])
        arcpy.SelectLayerByAttribute_management("IPA_lyr", "NEW_SELECTION", '"FID" = {0}'.format(row[0]))
        arcpy.CopyFeatures_management("IPA_lyr", "Individual IPAs/{0}_IPA.shp".format(newName))

# 4) Make each cluster of IPA_Plants for an individual IPA its own shapefile:
patternFinder = re.compile('[\W]+')
arcpy.MakeFeatureLayer_management(IPA_plants, "IPA_plants_lyr")
with arcpy.da.SearchCursor(IPA_plants, ["Site_Name"]) as cursor:
    for row in cursor:
        newName = patternFinder.sub("", row[0])
        arcpy.SelectLayerByAttribute_management("IPA_plants_lyr", "NEW_SELECTION", '"Site_Name" = ' + "'{0}'".format(row[0]))
        arcpy.CopyFeatures_management("IPA_plants_lyr", "IPA Plants by IPA/{0}_Plants.shp".format(newName))