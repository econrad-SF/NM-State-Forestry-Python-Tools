#-------------------------------------------------------------------------------
# Name:        Populate the Unique ID Field
'''
Purpose:     This script creates an update cursor to loop through the "Orig_Name"
and "Unique_ID" columns of a feature class. It uses a regular expression to find
and grab the unique ID that has been appended to the Orig_Name value, and populates
the unique ID to the Unique ID attribute.
'''
# Author:      Ed Conrad
# Created:     10/07/2017
# Copyright:   (c) Ed Conrad 2017
# Licence:     ArcGIS 10.4
#-------------------------------------------------------------------------------
import arcpy, os, re
year = "2018"
fc = r"OARS Temp/OARS_Temp.gdb/OARS_Treatments_{0}".format(year)

# Create Search Cursor to loop through "Orig_Name" and "Unique_ID" fields
with arcpy.da.UpdateCursor(fc, ["Orig_Name", "Unique_ID"]) as cursor:
    for row in cursor:
        orig_name = row[0]

        ####  RegEX Part ###
        # Check to see if name has '_proj' in it, if so remove it from match object
        pattern1 = re.compile(r'_proj')
        firstMatch = pattern1.sub('', orig_name)

        # Use 2nd Regex to search for and match last '_' with 1-4 numbers followed by '.shp'. '\d+' = (one digit or more); '$' = (match made from end of string)
        pattern2 = re.compile(r'_\d+\.shp$')
        secondMatch = pattern2.findall(firstMatch) # secondMatch is a list object

        # convert list to string and use 2nd Regex to search for '_proj'. If it exists, remove it.
        secondMatch = ''.join(secondMatch)

        # Return just the unique ID; Unique ID is a numeric data type and ready to be populated into "Unique_ID" field of shapefile.
        uniqueID = secondMatch[1:-4]
        ###################

        # Provide logic whether a match was even made (early OARS didn't have Unique ID)
        # If match is made, populate the Unique ID found by the RegEx in the Unique_ID column, else do nothing
        if uniqueID:
            row[1] = uniqueID
            cursor.updateRow(row)
        else:
            pass
