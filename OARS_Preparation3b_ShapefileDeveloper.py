#-------------------------------------------------------------------------------
# Name:        OARS Prep Tool #3
''' Purpose:  Prior to running this tool, take the output of script 2, open the
              attribute table, select the rows that used the OARS Shapefile Developer,
              and export them as a new shapefile. Then use this tool to move file
              into OARS_Temp.gdb and slightly change order of columns and give aliases.
              Prior to 2017, you wouldn't need to use this script since it's specifically
              adapted for shapefiles that went through the OARS Shapefile Developer.
'''
# Author:      Ed Conrad
# Created:     September 12, 2017
# Copyright:   (c) Ed Conrad 2017
#----------------------------------------------------------------------------------------------------------------- Instructions for Use ------------------------ # Need to Change 1 thing to run
import arcpy, os, datetime
from arcpy import env
tempData = os.path.join(os.getcwd(), "OARS Temp")
env.workspace = os.path.join(tempData, "OARS_Temp.gdb")
env.overwriteOutput = False
year = "2018"                                                                   # <-------------------------------------------------------------------------------- (1) Change Year

# Bring Shapefile into Geodatabase
shapefile = "Treatments_{0}_merge.shp".format(year)
featureClass = "Treatments_{0}_merge".format(year)
arcpy.CopyFeatures_management(os.path.join(tempData, shapefile), featureClass)
arcpy.Rename_management(featureClass, "Treatments")
fc = "Treatments"

# "Shape_Length" and "Shape_Area" are required fields, but unfortunately are not in the order that I need to match OARS template (cannot delete these and simply add them again); Work-around below.
arcpy.MakeQueryTable_management(fc, "QueryTable", "USE_KEY_FIELDS", "", "Treatments.OBJECTID; Treatments.Shape; Treatments.Orig_Name; Treatments.ProjectNam; Treatments.GrantTitle; Treatments.FundNumber; Treatments.Coop_ID; Treatments.WkplanNum; Treatments.District; Treatments.Landowner; Treatments.AgencyInv; Treatments.CWPP; Treatments.CARS; Treatments.ForestType; Treatments.Treatment; Treatments.AccompDate; Treatments.Input_Date; Treatments.FY; Treatments.Acres")
arcpy.CopyFeatures_management("QueryTable", "Treatments_Edited")
arcpy.Delete_management("QueryTable")
arcpy.Delete_management("Treatments")                                           # This step & the next allow me to keep original "Treatments" name
arcpy.Rename_management("Treatments_Edited", "Treatments")

# Another cleanup - MakeQueryTable function corrects the order of "Shape_Length" & "Shape_Area", but unfortunately changes the FC's field names & aliases.
arcpy.AlterField_management(fc, "Treatments_Orig_Name", "Orig_Name", "Original Shapefile Name")
arcpy.AlterField_management(fc, "Treatments_ProjectNam", "ProjectNam", "Project Name")
arcpy.AlterField_management(fc, "Treatments_GrantTitle", "GrantTitle", "Grant Title")
arcpy.AlterField_management(fc, "Treatments_FundNumber", "FundNumber", "Fund Number")
arcpy.AlterField_management(fc, "Treatments_Coop_ID", "Coop_ID", "Cooperator ID")
arcpy.AlterField_management(fc, "Treatments_WkplanNum", "WkplanNum", "Workplan Number")
arcpy.AlterField_management(fc, "Treatments_District", "District", "District")
arcpy.AlterField_management(fc, "Treatments_Landowner", "Landowner", "Landowner")
arcpy.AlterField_management(fc, "Treatments_AgencyInv", "AgencyInv", "Agencies Involved")
arcpy.AlterField_management(fc, "Treatments_CWPP", "CWPP", "Community Wildfire Protection Plan")
arcpy.AlterField_management(fc, "Treatments_CARS", "CARS", "Communities at Risk")
arcpy.AlterField_management(fc, "Treatments_ForestType", "ForestType", "Forest Type")
arcpy.AlterField_management(fc, "Treatments_Treatment", "Treatment", "Treatment")
arcpy.AlterField_management(fc, "Treatments_AccompDate", "AccompDate", "Accomplishment Date")
arcpy.AlterField_management(fc, "Treatments_Input_Date", "Input_Date", "Input Date")
arcpy.AlterField_management(fc, "Treatments_FY", "FY", "FY")
arcpy.AlterField_management(fc, "Treatments_Acres", "Acres", "Acres")

cursor = arcpy.da.UpdateCursor(fc, ["CWPP"])
for row in cursor:
    name = row[0]
    counties = ['Bernalillo', 'Catron', 'Chaves', 'Cibola', 'Colfax', 'Curry', 'De Baca', 'Dona Ana', 'Eddy', 'Grant', 'Guadalupe', 'Harding',\
    'Hidalgo', 'Lea', 'Lincoln', 'Los Alamos', 'Luna', 'McKinley', 'Mora', 'Otero', 'Quay', 'Rio Arriba', 'Roosevelt', 'San Juan', 'San Miguel',\
    'Sandoval', 'Santa Fe', 'Sierra', 'Socorro', 'Taos', 'Torrance', 'Union', 'Valencia']
    if name.title() in counties:
        row[0] = name + " County"
        cursor.updateRow(row)
    else: pass
del row, cursor

# Provide a new name for the feature class in the OARS_Temp.gdb   May need to change the name to "_new" if you're adding new shapefiles for 2018 FY since there
# will already be a feature class named "OARS_Treatments_2018"
arcpy.Rename_management("Treatments", "OARS_Treatments_{0}".format(year))
print("OARS_Preparation3b_ShapefileDeveloper.py script ran successfully.")