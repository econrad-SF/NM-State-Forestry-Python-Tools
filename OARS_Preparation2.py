#-------------------------------------------------------------------------------
# Name:        OARS Prep Tool #2
# Purpose:     This script merges all OARS shapefiles. The output of
#              this script is a feature class called "Treatments_16_merge.shp".
#
# Author:      Ed Conrad
# Created:     Feb. 16, 2017
# Copyright:   (c) Ed Conrad 2017
#----------------------------------------------------------------------------------------------------------------- Instructions for Use ------------ # Need to Change 1 thing to run
import arcpy, os
from arcpy import env
tempData = os.path.join(os.getcwd(), "OARS Temp")
year = "2018"                                                                   # <-------------------------------------------------------------------------------- (1) Change Year
folder = "OARS Raw Data\OARS S_FY{0}".format(year[2:])
env.workspace = os.path.join(os.getcwd(), folder)
env.overwriteOutput = False
env.outputZFlag = "Disabled"                                                    # disable so after merge management, values in 'Shape' field will be 'Polygon'
env.outputMFlag = "Disabled"                                                    # rather than mixture of 'Polygon', 'Polygon Z', & 'Polygon M'

shapefile = "Treatments_{0}_merge.shp".format(year)


fclist = arcpy.ListFeatureClasses()
fieldMappings = arcpy.FieldMappings()                                           # Create FieldMappings object to manage merge output fields
for fc in fclist:
    fieldMappings.addTable(fc)                                                  # Add all fields to each shapefile (necessary to specify which fields to keep below)

# Remove all output fields from the field mappings, except the following fields if they're present.
for field in fieldMappings.fields:
    if field.name not in ["Landowner", "Project", "Agencies", "Acres", "Funding", "CWPP", "All_CARS", "Treatment", "ProjectNum", "District", "Forest_Typ",\
    "WP_Num", "InputDate", "ProjectNam", "GrantTitle", "FundNumber", "Coop_ID", "WkplanNum", "District", "AgencyInv", "CARS", "ForestType", "AccompDate", "Input_Date", "FY", "Orig_Name", "Veg_Type"]:
        fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(field.name))

    # ERROR Warning. I discovered 2 shapefiles in FY16 that had the attribute "Forest_Typ" defined with a length of 20. Subsequent shapefiles that have this
    # field give it a length of 50. An error will occur when merge management is performed b/c the 1st shapefile to have this field, had length of 20, not 50.
    # Bad Shapefiles:
    #    "BLM_PAagreement_ready_for_payment_5480"
    # 1) "15_SEV_TAX_A141584_1256_USFS_3992.shp"
    # 2) "EQIP_JUlibarri_091216_5475.shp"
    # 2) "Hazard_VII_report_file_2_4159.shp". I added the letter 'Z' to both file names, so they'd be merged at the end and the error wouldn't result.

    #!! 2017 FY - move BartleySouthernTract31acres_5820.... to front b/c it uses most recent data template with possibility of longest attribute fields.

arcpy.Merge_management(fclist, os.path.join(tempData, shapefile), fieldMappings)
print("Script OARS_Preparation2.py successful. Merge complete.")