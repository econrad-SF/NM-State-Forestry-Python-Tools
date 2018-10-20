import arcpy, csv, os, re
from arcpy import env
from datetime import datetime, date
now = datetime.now()

class Toolbox(object):
    def __init__(self):
        self.label = "Forestry GIS Tools"
        self.description = "This toolbox contains custom GIS tools created specifically for NM State Forestry. Preexisting custom tools will be incoorporated into this toolbox over time."
        self.tools = [E911_Analysis, ForestHealth_ShapefileDeveloper, MapScale, OARS_Shapefile_Developer, PercentSlopeAnalysis, ShapefileToWKT]

class E911_Analysis(object):
    def __init__(self):
        self.label = "E911 Analysis - Fire Mapping"
        self.description = "This is a Fire Management tool that performs a E911 Analysis to quantify the number of E911 addresses that fall within a 1 mile or 5 mile buffer (optionally both) of a fire origin. The user provides \
        GPS coordinates of the fire origin in either decimal degrees or in degrees/minutes/seconds, and if a buffer option is selected, maps displaying the results are created (# of affected E911 addresses are displayed in \
        the map subtitle). Outputs from this tool include a KMZ file of the fire origin with attributes such as land ownership, township/range, county, date, and name that can be viewed in Google Earth . A geodatabase is also created that \
        contains the following: fire origin, fire buffers (1 mile, 5 mile, or both), E911 addresses that fall within selected buffers, Land Ownership within the buffer (acreage is calculated by ownership and viewable in the \
        attribute table). Lastly, a mxd file can optionally be saved if you want to make your own fire maps using outputs from this tool."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Latitude (Degrees-minutes-seconds)",
            name = "Latitude_dms",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input")
        param1 = arcpy.Parameter(
            displayName = "Longitude (Degrees-minutes-seconds)",
            name = "Longitude_dms",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input")
        param2 = arcpy.Parameter(
            displayName = "Latitude (Decimal degrees)",
            name = "Latitude_dd",
            datatype = "GPDouble",
            parameterType = "Required",
            direction = "Input")
        param3 = arcpy.Parameter(
            displayName = "Longitude (Decimal degrees)",
            name = "Longitude_dd",
            datatype = "GPDouble",
            parameterType = "Required",
            direction = "Input")
        param4 = arcpy.Parameter(
            displayName = "Fire Name",
            name = "Fire Name",
            datatype = "GPString",
            parameterType = "GPString",
            direction = "Input")
        param5 = arcpy.Parameter(
            displayName="Output Folder",
            name="Output_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param6 = arcpy.Parameter(
            displayName = "Create 1 mile Fire Buffer?",
            name = "Create 1 mile Fire Buffer?",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")
        param7 = arcpy.Parameter(
            displayName = "Create 5 mile Fire Buffer?",
            name = "Create 5 mile Fire Buffer?",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")
        param8 = arcpy.Parameter(
            displayName = "Save MXD file(s)?",
            name = "Save MXD file(s)?",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")

        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[0].altered:
            dms = parameters[0].value
            dms_list = dms.split()
            lat_decimalDegrees = float(dms_list[0]) + (float(dms_list[1])/60) + (float(dms_list[2])/3600)
            parameters[2].value = round(lat_decimalDegrees, 6)
        else: pass
        if parameters[1].altered:
            dms = parameters[1].value
            dms_list = dms.split()
            long_decimalDegrees = -abs(float(dms_list[0]) + (float(dms_list[1])/60) + (float(dms_list[2])/3600))
            parameters[3].value = round(long_decimalDegrees, 6)
        else: pass
        return

    def updateMessages(self, parameters):
        if 31.32 <= parameters[2].value <= 37:
            arcpy.AddMessage("Value is OK.")
        else:
            parameters[2].setErrorMessage(str("Latitude entered is outside of New Mexico."))
        if -109.05 <= parameters[3].value <= -103.02:
            arcpy.AddMessage("Value is OK.")
        else:
            parameters[3].setErrorMessage(str("Longitude entered is outside of New Mexico. Also, be sure that you've provided a negative before longitude."))
        return

    def execute(self, parameters, messages):
        # User-provided input
        latitude = parameters[2].value
        longitude = parameters[3].value
        fire = parameters[4].valueAsText
        patternFinder = re.compile('[\W]+')
        fireName = patternFinder.sub("", fire)
        folder = parameters[5].valueAsText
        buffer1mile = parameters[6].value
        buffer5mile = parameters[7].value

        # Script Reference Files
        referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\E911 Analysis")
        e911 = os.path.join(referenceFiles, "Addresses_E911.shp")
        ownership = os.path.join(referenceFiles, "E911_Land_Ownership.shp")
        counties = os.path.join(referenceFiles, "E911_County.shp")
        district = os.path.join(referenceFiles, "E911_NMSF_Districts.shp")
        township_range = os.path.join(referenceFiles, "E911_Township.shp")
        fireOrigin_lyr = os.path.join(referenceFiles, "Fire_Origin.lyr")
        buffer_lyr = os.path.join(referenceFiles, "Buffer.lyr")
        e911_lyr = os.path.join(referenceFiles, "E911_Addresses.lyr")

        # Set Spatial Refernce Variable for Feature Dataset
        WGS84 = arcpy.SpatialReference("WGS 1984")
        NAD83 = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")

        # Create Geodatabase
        arcpy.SetProgressor("default", "Peforming E911 fire analysis...")
        arcpy.CreateFileGDB_management(folder, fireName + ".gdb")
        gdb = r"{0}\{1}.gdb".format(folder, fireName)
        arcpy.CreateFeatureDataset_management(gdb, "WGS84", WGS84)
        arcpy.CreateFeatureDataset_management(gdb, "NAD83", NAD83)

        # Create new CSV file and populate it with lat/long from user input
        with open("{0}/{1}.csv".format(folder, fireName), 'w') as csvfile:
            fieldnames = ['Latitude', 'Longitude']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({'Latitude': latitude, 'Longitude': longitude})
        table = "{0}/{1}.csv".format(folder, fireName)

        temp_layer = "{0}_temp".format(fireName)
        arcpy.MakeXYEventLayer_management(table, "Longitude", "Latitude", temp_layer, WGS84)
        arcpy.CopyFeatures_management(temp_layer, "{0}/WGS84/{1}_temp".format(gdb, fireName))
        fc = "{0}/WGS84/{1}_temp".format(gdb, fireName)

        # Reproject Fire Origin to NAD83 datum UTM Zone 13N
        arcpy.Project_management(fc, "{0}/NAD83/{1}_proj".format(gdb, fireName), NAD83, "WGS_1984_(ITRF00)_To_NAD_1983")
        fc_proj = "{0}/NAD83/{1}_proj".format(gdb, fireName)

        # Add fields to Fire Origin Shapefile
        arcpy.SetProgressorLabel("Adding attributes to fire origin shapefile...")
        arcpy.AddField_management(fc_proj, "FireName", "TEXT", "", "", 30, "Fire Name")
        arcpy.AddField_management(fc_proj, "FireDate", "DATE", "", "", "", "Fire Date")
        arcpy.CalculateField_management(fc_proj, "FireName", '"' + str(fire) + '"', "PYTHON")
        nowEsri = now.strftime("%m/%d/%Y %H:%M:%S %p")
        arcpy.CalculateField_management(fc_proj, "FireDate", '"' + nowEsri + '"', "PYTHON")

        # Overlay analysis to get desired fire origin attributes: ownership, county, NMSF district, township/range    # Basic & Standard ArcGIS license only allow two fc's for Intersect analysis...   #arcpy.Intersect_analysis([fc_proj, ownership, counties, district, township_range], "{0}/NAD83/{1}_Fire_Origin".format(gdb, fireName), "NO_FID", "", "INPUT")
        temp1 = "{0}/NAD83/temp1".format(gdb)
        temp2 = "{0}/NAD83/temp2".format(gdb)
        temp3 = "{0}/NAD83/temp3".format(gdb)
        arcpy.Intersect_analysis([fc_proj, ownership], "{0}/NAD83/temp1".format(gdb), "NO_FID")
        arcpy.Intersect_analysis([temp1, counties], "{0}/NAD83/temp2".format(gdb), "NO_FID")
        arcpy.Intersect_analysis([temp2, district], "{0}/NAD83/temp3".format(gdb), "NO_FID")
        arcpy.Intersect_analysis([temp3, township_range], "{0}/NAD83/{1}_Fire_Origin".format(gdb, fireName), "NO_FID")

        # Allow logic to account whether PLSS township/range exists at the location of the point (Intersect_analysis above would create a feature class, but it would have zero geomtry and attributes if point overlaps gap).
        if arcpy.management.GetCount("{0}/NAD83/{1}_Fire_Origin".format(gdb, fireName))[0] == "0":
            arcpy.AddMessage("FYI - The location of this fire doesn't overlap any PLSS township/range (there are gaps in PLSS coverage in New Mexico), so these attributes won't be included with either {0}.kmz or {1}\NAD83\{2}_Fire_Origin.".format(fireName, gdb, fireName))
            arcpy.Delete_management("{0}/NAD83/{1}_Fire_Origin".format(gdb, fireName))
            arcpy.Rename_management("{0}/NAD83/temp2".format(gdb), "{0}/NAD83/{1}_Fire_Origin".format(gdb, fireName))    # June edits
        else: pass
        fire_origin = "{0}/NAD83/{1}_Fire_Origin".format(gdb, fireName)

        # Perform 1 Mile E911 Buffer Analysis Create Map if User Selects Box
        if parameters[6].altered:
            # Create new files
            buffer1mile = "{0}/NAD83/Buffer_1mile".format(gdb)
            e911_1mile = "{0}/NAD83/E911_Addresses_1mile".format(gdb)
            own_temp1 = "{0}/NAD83/Ownership_temp1".format(gdb)
            own_final1 = "{0}/NAD83/Ownership_1mileBuffer".format(gdb)

            # Analysis
            arcpy.SetProgressorLabel("Performing 1 mile buffer E911 analysis...")
            arcpy.Buffer_analysis(fc_proj, buffer1mile, "1 Miles")
            arcpy.Clip_analysis(e911, buffer1mile, e911_1mile)
            arcpy.AddField_management(fire_origin, "Addresses1", "LONG", "", "", "", "E911 Addresses within 1 mile")
            count = arcpy.management.GetCount(e911_1mile)
            arcpy.CalculateField_management(fire_origin, "Addresses1", count, "PYTHON")
            arcpy.Clip_analysis(ownership, buffer1mile, own_temp1)
            arcpy.Dissolve_management(own_temp1, "{0}/NAD83/Ownership_1mileBuffer".format(gdb), "Ownership")
            arcpy.AddField_management(own_final1, "Acres", "Double")
            arcpy.CalculateField_management(own_final1, "Acres", "!shape.area@acres!", "PYTHON")

            ####################################################################
            # Create Map
            ####################################################################
            arcpy.SetProgressorLabel("Creating {0}_1mileBuffer.pdf map...".format(fireName))
            mxd_template = arcpy.mapping.MapDocument(os.path.join(referenceFiles, "fire_basemap.mxd"))
            Output_1mile_mxd = "{0}/{1}_1mile_{2}_{3}_{4}.mxd".format(folder, fireName, now.month, now.day, now.year)
            df_main = arcpy.mapping.ListDataFrames(mxd_template, "Main Map")[0]

            # Make sure map doesn't have layers from running previously
            for lyr in arcpy.mapping.ListLayers(mxd_template, "*", df_main):
            # Begin by removing layers if 1 mile map was created by running tool in succession.
                if lyr.name == "{0}".format(fire):
                    arcpy.mapping.RemoveLayer(df_main, lyr)
                elif lyr.name == "E911 Addresses in Extent":
                    arcpy.mapping.RemoveLayer(df_main, lyr)
                elif lyr.name == "Buffer - 1 mile":
                    arcpy.mapping.RemoveLayer(df_main, lyr)

            # Convert shapefiles to layers, add them to mxd, & change symbology
            # Buffer - 1 mile Layer
            arcpy.MakeFeatureLayer_management(buffer1mile, "buffer1mile")
            buffer1 = arcpy.mapping.Layer("buffer1mile")
            arcpy.mapping.AddLayer(df_main, buffer1, "TOP")
            updateLayer = arcpy.mapping.ListLayers(mxd_template, buffer1, df_main)[0]
            sourceLayer = arcpy.mapping.Layer(buffer_lyr)
            arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)
            # E911 Addresses Layer
            arcpy.MakeFeatureLayer_management(e911_1mile, "e911")
            e911_1 = arcpy.mapping.Layer("e911")
            arcpy.mapping.AddLayer(df_main, e911_1, "TOP")
            updateLayer = arcpy.mapping.ListLayers(mxd_template, e911_1, df_main)[0]
            sourceLayer = arcpy.mapping.Layer(e911_lyr)
            arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)
            # Fire Origin Layer
            arcpy.MakeFeatureLayer_management(fire_origin, "{0}".format(fireName))
            fireOrigin = arcpy.mapping.Layer("{0}".format(fireName))
            arcpy.mapping.AddLayer(df_main, fireOrigin, "TOP")
            updateLayer = arcpy.mapping.ListLayers(mxd_template, fireOrigin, df_main)[0]    # the map layer object
            sourceLayer = arcpy.mapping.Layer(fireOrigin_lyr)
            arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)

            # Change layer Names for legend entry
            for lyr in arcpy.mapping.ListLayers(mxd_template, "*", df_main):
                if lyr.name == "{0}".format(fireName):
                    lyr.name = "{0}".format(fire)
                elif lyr.name == "e911":
                    lyr.name = "E911 Addresses in Buffer"
                elif lyr.name == "buffer1mile":
                    lyr.name = "Buffer - 1 mile"

            # Zoom Main Map extent to Fire Buffer
            Extent = buffer1.getExtent(True)
            df_main.extent = Extent
            df_main.scale = 20000   # Zoom out map so map text can read 1 cm = 200 meters

            # Update map elements
            newTitle = fire

            # Format Subtitle - subtitle will state the number of affected E911 Addresses
            result = arcpy.GetCount_management(e911_1)
            e911_sum = list(str(int(result.getOutput(0))))
            if len(e911_sum) == 4:
                e911_sum.insert(1, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 5:
                e911_sum.insert(2, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 6:
                e911_sum.insert(3, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 7:
                e911_sum.insert(1, ',')
                e911_sum.insert(4, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 8:
                e911_sum.insert(2, ',')
                e911_sum.insert(5, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 9:
                e911_sum.insert(3, ',')
                e911_sum.insert(6, ',')
                e911_sumFormatted = ''.join(e911_sum)
            else:
                e911_sumFormatted = ''.join(e911_sum)
            date1 = now.strftime("%m/%d/%y")
            newSubtitle = "{0}; E911 Addresses in 1 mile Buffer: {1}".format(date1, e911_sumFormatted)
            date2 = now.strftime("%B %d, %Y")
            newMapNotes = "{0} {1}\n{2}".format("NMSF", date2, "NAD83 UTM Zone 13N")
            myElements = arcpy.mapping.ListLayoutElements(mxd_template, "TEXT_ELEMENT")
            for element in myElements:
                if element.name == "Map Title":
                    element.text = newTitle
                elif element.name == "Map Subtitle":
                    element.text = newSubtitle
                elif element.name == "Map Notes":
                    element.text = newMapNotes

            # Format scale bar & scale bar text (e.g., 1:100,000 1 inch = 1.58 miles)
            # 1a) Specify Scale Bar as meters or miles dependent on data frame scale.
            met_scale = arcpy.mapping.ListLayoutElements(mxd_template, "MAPSURROUND_ELEMENT", "Scale Bar - meters")[0]
            mil_scale = arcpy.mapping.ListLayoutElements(mxd_template, "MAPSURROUND_ELEMENT", "Scale Bar - miles")[0]
            if df_main.scale < 25000:
                met_scale.elementPositionX = 1.936    # On the page
                mil_scale.elementPositionX = 15       # Move scale bar off the page
            else:
                met_scale.elementPositionX = 15
                mil_scale.elementPositionX = 1.936

            # 1b) Format the text below scale bar by putting in commas for thousand dividers.
            scaleList = list(str(int(df_main.scale)))
            if len(scaleList) == 4:
                scaleList.insert(1, ',')
                scaleFormatted = ''.join(scaleList)
            elif len(scaleList) == 5:
                scaleList.insert(2, ',')
                scaleFormatted = ''.join(scaleList)
            elif len(scaleList) == 6:
                scaleList.insert(3, ',')
                scaleFormatted = ''.join(scaleList)
            else:
                pass

            # 1c) Specify scale bar in meters
            scaleText = arcpy.mapping.ListLayoutElements(mxd_template, "TEXT_ELEMENT", "Scale Text")[0]
            meters = df_main.scale/100
            scaleText.text = "Scale: 1:{0}  1 cm = {1} meters".format(scaleFormatted, str(int(meters)))

            # Save then export mapdocument to PDF
            arcpy.SetProgressorLabel("Now saving {0}_1mileBuffer.pdf at your chosen folder: {1}. This step takes awhile...".format(fireName, folder))
            mxd_template.saveACopy(Output_1mile_mxd)
            arcpy.mapping.ExportToPDF(mxd_template, "{0}/{1}_1mileBuffer.pdf".format(folder, fireName))
            os.startfile("{0}/{1}_1mileBuffer.pdf".format(folder, fireName))

            # Cleanup
            del mxd_template
            arcpy.Delete_management("{0}/{1}.gdb/NAD83/Ownership_temp1".format(folder, fireName))
            deleteFields = ['BUFF_DIST', 'ORIG_FID']
            arcpy.DeleteField_management(buffer1mile, deleteFields)

            # Does user choose to save mxd file?
            if parameters[8].altered:
                pass
            else:
                arcpy.Delete_management(Output_1mile_mxd)
        else: pass

        # Perform 5 Mile E911 Buffer Analysis and Create Map if User Selects Box
        if parameters[7].altered:
            # Create new files
            buffer5mile = "{0}/NAD83/Buffer_5mile".format(gdb)
            e911_5mile = "{0}/NAD83/E911_Addresses_5mile".format(gdb)
            own_temp5 = "{0}/NAD83/Ownership_temp5".format(gdb)
            own_final5 = "{0}/NAD83/Ownership_5mileBuffer".format(gdb)

            # Analysis
            arcpy.Buffer_analysis(fc_proj, buffer5mile, "5 Miles")
            arcpy.Clip_analysis(e911, buffer5mile, e911_5mile)
            arcpy.AddField_management(fire_origin, "Addresses5", "LONG", "", "", "", "E911 Addresses within 5 miles")
            count = arcpy.management.GetCount(e911_5mile)
            arcpy.CalculateField_management(fire_origin, "Addresses5", count, "PYTHON")
            arcpy.Clip_analysis(ownership, buffer5mile, own_temp5)
            arcpy.Dissolve_management(own_temp5, "{0}/NAD83/Ownership_5mileBuffer".format(gdb), "Ownership")
            arcpy.AddField_management(own_final5, "Acres", "Double")
            arcpy.CalculateField_management(own_final5, "Acres", "!shape.area@acres!", "PYTHON")

            # Create Map
            arcpy.SetProgressorLabel("Creating {0}_5mileBuffer.pdf map...".format(fireName))
            mxd_template = arcpy.mapping.MapDocument(os.path.join(referenceFiles, "fire_basemap.mxd"))   # Reference the original template again.
            Output_5mile_mxd = "{0}/{1}_5mile_{2}_{3}_{4}.mxd".format(folder, fireName, now.month, now.day, now.year)
            df_main = arcpy.mapping.ListDataFrames(mxd_template, "Main Map")[0]

            # Make sure map doesn't have layers from running previously
            for lyr in arcpy.mapping.ListLayers(mxd_template, "*", df_main):
            # Begin by removing layers if 1 mile map was created in previous step
                if lyr.name == "{0}".format(fire):
                    arcpy.mapping.RemoveLayer(df_main, lyr)
                elif lyr.name == "E911 Addresses in Buffer":
                    arcpy.mapping.RemoveLayer(df_main, lyr)
                elif lyr.name == "Buffer - 1 mile":
                    arcpy.mapping.RemoveLayer(df_main, lyr)
            # Buffer Layer
            arcpy.MakeFeatureLayer_management(buffer5mile, "buffer5mile")
            buffer5 = arcpy.mapping.Layer("buffer5mile")
            arcpy.mapping.AddLayer(df_main, buffer5, "TOP")
            updateLayer = arcpy.mapping.ListLayers(mxd_template, buffer5, df_main)[0]
            sourceLayer = arcpy.mapping.Layer(buffer_lyr)
            arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)
            # E911 Addresses Layer
            arcpy.MakeFeatureLayer_management(e911_5mile, "e911_2")
            e911_5 = arcpy.mapping.Layer("e911_2")
            arcpy.mapping.AddLayer(df_main, e911_5, "TOP")
            updateLayer = arcpy.mapping.ListLayers(mxd_template, e911_5, df_main)[0]
            sourceLayer = arcpy.mapping.Layer(e911_lyr)
            arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)
            # Fire Origin Layer
            arcpy.MakeFeatureLayer_management(fire_origin, "{0}_2".format(fireName))
            fireOrigin = arcpy.mapping.Layer("{0}_2".format(fireName))
            arcpy.mapping.AddLayer(df_main, fireOrigin, "TOP")
            updateLayer = arcpy.mapping.ListLayers(mxd_template, fireOrigin, df_main)[0]    # the map layer object
            sourceLayer = arcpy.mapping.Layer(fireOrigin_lyr)
            arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)

            # Change layer Names for legend entry
            for lyr in arcpy.mapping.ListLayers(mxd_template, "*", df_main):
                if lyr.name == "{0}_2".format(fireName):
                    lyr.name = "{0}".format(fire)
                elif lyr.name == "e911_2":
                    lyr.name = "E911 Addresses in Buffer"
                elif lyr.name == "buffer5mile":
                    lyr.name = "Buffer - 5 mile"

            # Zoom Main Map extent to Fire Buffer
            Extent = buffer5.getExtent(True)
            df_main.extent = Extent
            df_main.scale = 95040   # Zoom map so that map text can be 1 inch = 1.5 miles

            # Update map elements
            newTitle = fire

            # Format Subtitle - subtitle will state the number of affected E911 Addresses
            result = arcpy.GetCount_management(e911_5)
            e911_sum = list(str(int(result.getOutput(0))))
            if len(e911_sum) == 4:
                e911_sum.insert(1, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 5:
                e911_sum.insert(2, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 6:
                e911_sum.insert(3, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 7:
                e911_sum.insert(1, ',')
                e911_sum.insert(4, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 8:
                e911_sum.insert(2, ',')
                e911_sum.insert(5, ',')
                e911_sumFormatted = ''.join(e911_sum)
            elif len(e911_sum) == 9:
                e911_sum.insert(3, ',')
                e911_sum.insert(6, ',')
                e911_sumFormatted = ''.join(e911_sum)
            else:
                e911_sumFormatted = ''.join(e911_sum)
            date1 = now.strftime("%m/%d/%y")
            newSubtitle = "{0}; E911 Addresses in 5 mile Buffer: {1}".format(date1, e911_sumFormatted)
            date2 = now.strftime("%B %d, %Y")
            newMapNotes = "{0} {1}\n{2}".format("NMSF", date2, "NAD83 UTM Zone 13N")
            myElements = arcpy.mapping.ListLayoutElements(mxd_template, "TEXT_ELEMENT")
            for element in myElements:
                if element.name == "Map Title":
                    element.text = newTitle
                elif element.name == "Map Subtitle":
                    element.text = newSubtitle
                elif element.name == "Map Notes":
                    element.text = newMapNotes

            # Format scale bar & scale bar text (e.g., 1:100,000 1 inch = 1.58 miles)
            # 1a) Specify Scale Bar as meters or miles dependent on data frame scale.
            met_scale = arcpy.mapping.ListLayoutElements(mxd_template, "MAPSURROUND_ELEMENT", "Scale Bar - meters")[0]
            mil_scale = arcpy.mapping.ListLayoutElements(mxd_template, "MAPSURROUND_ELEMENT", "Scale Bar - miles")[0]
            if df_main.scale < 25000:
                met_scale.elementPositionX = 1.936    # On the page
                mil_scale.elementPositionX = 15       # Move scale bar off the page
            else:
                met_scale.elementPositionX = 15
                mil_scale.elementPositionX = 1.936

            # 1b) Format the text below scale bar by putting in commas for thousand dividers.
            scaleList = list(str(int(df_main.scale)))
            if len(scaleList) == 4:
                scaleList.insert(1, ',')
                scaleFormatted = ''.join(scaleList)
            elif len(scaleList) == 5:
                scaleList.insert(2, ',')
                scaleFormatted = ''.join(scaleList)
            elif len(scaleList) == 6:
                scaleList.insert(3, ',')
                scaleFormatted = ''.join(scaleList)
            else:
                pass

            # 1c) Specify scale bar in miles using map scale.
            scaleText = arcpy.mapping.ListLayoutElements(mxd_template, "TEXT_ELEMENT", "Scale Text")[0]
            feet = df_main.scale/12   # Convert inches to feet
            miles = feet/5280          # Convert feet to miles
            scaleText.text = "Scale: 1:{0}  1 inch = {1} miles".format(scaleFormatted, str(round(miles,2)))

            # Save then export mapdocument to PDF
            arcpy.SetProgressorLabel("Now saving {0}_5mileBuffer.pdf at your chosen folder: {1}. This step takes awhile...".format(fireName, folder))
            mxd_template.saveACopy(Output_5mile_mxd)
            arcpy.mapping.ExportToPDF(mxd_template, "{0}/{1}_5mileBuffer.pdf".format(folder, fireName))
            os.startfile("{0}/{1}_5mileBuffer.pdf".format(folder, fireName))

            # Cleanup
            del mxd_template
            arcpy.Delete_management("{0}/NAD83/Ownership_temp5".format(gdb))
            deleteFields = ['BUFF_DIST', 'ORIG_FID']
            arcpy.DeleteField_management(buffer5mile, deleteFields)

            # Does user choose to save mxd file?
            if parameters[8].altered:
                pass
            else:
                arcpy.Delete_management(Output_5mile_mxd)
        else: pass

        # Create KMZ file
        mxd_template = arcpy.mapping.MapDocument(os.path.join(referenceFiles, "fire_basemap.mxd"))
        arcpy.MakeFeatureLayer_management(fire_origin, "{0}_3".format(fireName))
        fireOrigin = arcpy.mapping.Layer("{0}_3".format(fireName))
        fireOrigin.name = "{0}".format(fireName)
        arcpy.mapping.AddLayer(df_main, fireOrigin, "TOP")
        updateLayer = arcpy.mapping.ListLayers(mxd_template, fireOrigin, df_main)[0]    # the map layer object
        sourceLayer = arcpy.mapping.Layer(fireOrigin_lyr)
        arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)
        # Save Fire Origin as KMZ file
        fire_kml = arcpy.mapping.ListLayers(mxd_template, fireOrigin, df_main)[0]
        arcpy.LayerToKML_conversion(fire_kml, "{0}/{1}.kmz".format(folder, fireName), "", "NO_COMPOSITE", "", "", "", "CLAMPED_TO_GROUND")
        del mxd_template

        # Final Cleanup - Remove WGS84 Feature Dataset, CSV file, Projected fire origin created prior to intersect analysis, temp1-3 created during intersect analysis, and E911 Address feature classes if they're empty.
        arcpy.Delete_management("{0}/WGS84".format(gdb))
        arcpy.Delete_management("{0}/{1}.csv".format(folder, fireName))
        arcpy.Delete_management("{0}/NAD83/{1}_proj".format(gdb, fireName))
        arcpy.Delete_management("{0}/NAD83/temp1".format(gdb))
        arcpy.Delete_management("{0}/NAD83/temp2".format(gdb))
        if arcpy.Exists("{0}/NAD83/temp3".format(gdb)):
            arcpy.Delete_management("{0}/NAD83/temp3".format(gdb))
        if arcpy.Exists("{0}/NAD83/E911_Addresses_1mile".format(gdb)):
            if arcpy.management.GetCount("{0}/NAD83/E911_Addresses_1mile".format(gdb))[0] == "0":
                arcpy.Delete_management("{0}/NAD83/E911_Addresses_1mile".format(gdb))
        if arcpy.Exists("{0}/NAD83/E911_Addresses_5mile".format(gdb)):
            if arcpy.management.GetCount("{0}/NAD83/E911_Addresses_5mile".format(gdb))[0] == "0":
                arcpy.Delete_management("{0}/NAD83/E911_Addresses_5mile".format(gdb))
        return

class ForestHealth_ShapefileDeveloper(object):
    def __init__(self):
        self.label = "Forest Health Shapefile Developer"
        self.description = "This tool takes a shapefile/feature class provided by the USFS Forest Health program, and adds 18 new columns that correspond to existing columns.\
        These new columns have a description of what the original value was coded. For instance, column 'DCA1' has the new corresponding column 'DamageAg1' and value 11007 will now\
        equal 'Douglas-fir beetle'. It's possible that new codes not used previously will be added in subsquent years of surveys. When the code encounters a new value \
        the value in the new column will be 'Script Failed'. If 'Script Failed' is found in any row, adding the code and it's explanation to the script will remedy this. As of April\
        2017, many of the codes used can be found at the following link: https://www.fs.fed.us/foresthealth/technology/ads_standards.shtml   \
        One could also start an editing session and change the values to a few records that way."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Input Polygon",
            name = "Input Polygon",
            datatype = ["DEFeatureClass", "DEShapefile", "GPFeatureLayer"],                       # Set both Feature class & shapefile as acceptable inputs
            parameterType = "Required",
            direction = "Input")
        params = [param0]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # User-provided input
        shape = parameters[0].value

        # Add fields
        arcpy.AddField_management(shape, "Damage_Ag1", "TEXT", "", "", "35")
        arcpy.AddField_management(shape, "Damage_Ag2", "TEXT", "", "", "35")
        arcpy.AddField_management(shape, "Damage_Ag3", "TEXT", "", "", "35")
        arcpy.AddField_management(shape, "Host_Spec1", "TEXT", "", "", "25")
        arcpy.AddField_management(shape, "Host_Spec2", "TEXT", "", "", "25")
        arcpy.AddField_management(shape, "Host_Spec3", "TEXT", "", "", "25")
        arcpy.AddField_management(shape, "Frst_Type1", "TEXT", "", "", "50")
        arcpy.AddField_management(shape, "Frst_Type2", "TEXT", "", "", "50")
        arcpy.AddField_management(shape, "Frst_Type3", "TEXT", "", "", "50")
        arcpy.AddField_management(shape, "Pcnt_Mort1", "TEXT", "", "", "25")
        arcpy.AddField_management(shape, "Pcnt_Mort2", "TEXT", "", "", "25")
        arcpy.AddField_management(shape, "Pcnt_Mort3", "TEXT", "", "", "25")
        arcpy.AddField_management(shape, "Dmg_Typ1", "TEXT", "", "", "50")
        arcpy.AddField_management(shape, "Dmg_Typ2", "TEXT", "", "", "50")
        arcpy.AddField_management(shape, "Dmg_Typ3", "TEXT", "", "", "50")
        arcpy.AddField_management(shape, "Svrty_1", "TEXT", "", "", "45")
        arcpy.AddField_management(shape, "Svrty_2", "TEXT", "", "", "45")
        arcpy.AddField_management(shape, "Svrty_3", "TEXT", "", "", "45")
        rows = arcpy.UpdateCursor(shape)
        arcpy.env.overwriteOutput = True
        for row in rows:
            if row.DCA1 == 11007:
                row.Damage_Ag1 = "Douglas-fir beetle"
                rows.updateRow(row)
            elif row.DCA1 == 11009:
                row.Damage_Ag1 = "Spruce beetle"
                rows.updateRow(row)
            elif row.DCA1 == 11015:
                row.Damage_Ag1 = "Western balsam bark beetle"
                rows.updateRow(row)
            elif row.DCA1 == 11019:
                row.Damage_Ag1 = "Pinyon Ips"
                rows.updateRow(row)
            elif row.DCA1 == 11035:
                row.Damage_Ag1 = "Cedar bark beetles"
                rows.updateRow(row)
            elif row.DCA1 == 11050:
                row.Damage_Ag1 = "Fir engraver"
                rows.updateRow(row)
            elif row.DCA1 == 11900:
                row.Damage_Ag1 = "Unknown bark beetle"
                rows.updateRow(row)
            elif row.DCA1 == 12004:
                row.Damage_Ag1 = "Needleminers"
                rows.updateRow(row)
            elif row.DCA1 == 12005:
                row.Damage_Ag1 = "Sawflies"
                rows.updateRow(row)
            elif row.DCA1 == 12040:
                row.Damage_Ag1 = "Western spruce budworm"
                rows.updateRow(row)
            elif row.DCA1 == 12141:
                row.Damage_Ag1 = "Elm leaf beetle"
                rows.updateRow(row)
            elif row.DCA1 == 12123:
                row.Damage_Ag1 = "Douglas-fir tussock moth"
                rows.updateRow(row)
            elif row.DCA1 == 12239:
                row.Damage_Ag1 = "Tamarisk Leaf Beetles"
                rows.updateRow(row)
            elif row.DCA1 == 12800:
                row.Damage_Ag1 = "Other defoliator"
                rows.updateRow(row)
            elif row.DCA1 == 12900:
                row.Damage_Ag1 = "Unknown defoliator"
                rows.updateRow(row)
            elif row.DCA1 == 14029:
                row.Damage_Ag1 = "Pinyon needle scale"
                rows.updateRow(row)
            elif row.DCA1 == 25005:
                row.Damage_Ag1 = "Needlecast"
                rows.updateRow(row)
            elif row.DCA1 == 29002:
                row.Damage_Ag1 = "Sudden Aspen Decline"
                rows.updateRow(row)
            elif row.DCA1 == 50003:
                row.Damage_Ag1 = "Drought"
                rows.updateRow(row)
            elif row.DCA1 == 50013:
                row.Damage_Ag1 = "Wind-tornado/hurricane"
                rows.updateRow(row)
            elif row.DCA1 == 70008:
                row.Damage_Ag1 = "Mechanical"
                rows.updateRow(row)
            elif row.DCA1 == 71001:
                row.Damage_Ag1 = "Woodland cutting"
                rows.updateRow(row)
            elif row.DCA1 == 90000:
                row.Damage_Ag1 = "Unknown"
                rows.updateRow(row)
            elif row.DCA1 == 90009:
                rows.Damage_Ag1 = "Mortality"
                rows.updateRow(row)
            else:
                row.Damage_Ag1 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.DCA2 == 11007:
                row.Damage_Ag2 = "Douglas-fir beetle"
                rows.updateRow(row)
            elif row.DCA2 == 11009:
                row.Damage_Ag2 = "Spruce beetle"
                rows.updateRow(row)
            elif row.DCA2 == 11015:
                row.Damage_Ag2 = "Western balsam bark beetle"
                rows.updateRow(row)
            elif row.DCA2 == 11019:
                row.Damage_Ag2 = "Pinyon Ips"
                rows.updateRow(row)
            elif row.DCA2 == 11035:
                row.Damage_Ag2 = "Cedar bark beetles"
                rows.updateRow(row)
            elif row.DCA2 == 11050:
                row.Damage_Ag2 = "Fir engraver"
                rows.updateRow(row)
            elif row.DCA2 == 11900:
                row.Damage_Ag2 = "Unknown bark beetle"
                rows.updateRow(row)
            elif row.DCA2 == 12004:
                row.Damage_Ag2 = "Needleminers"
                rows.updateRow(row)
            elif row.DCA2 == 12005:
                row.Damage_Ag2 = "Sawflies"
                rows.updateRow(row)
            elif row.DCA2 == 12040:
                row.Damage_Ag2 = "Western spruce budworm"
                rows.updateRow(row)
            elif row.DCA2 == 12141:
                row.Damage_Ag2 = "Elm leaf beetle"
                rows.updateRow(row)
            elif row.DCA2 == 12123:
                row.Damage_Ag2 = "Douglas-fir tussock moth"
                rows.updateRow(row)
            elif row.DCA2 == 12239:
                row.Damage_Ag2 = "Tamarisk Leaf Beetles"
                rows.updateRow(row)
            elif row.DCA2 == 12800:
                row.Damage_Ag2 = "Other defoliator"
                rows.updateRow(row)
            elif row.DCA2 == 12900:
                row.Damage_Ag2 = "Unknown defoliator"
                rows.updateRow(row)
            elif row.DCA2 == 14029:
                row.Damage_Ag2 = "Pinyon needle scale"
                rows.updateRow(row)
            elif row.DCA2 == 25005:
                row.Damage_Ag2 = "Needlecast"
                rows.updateRow(row)
            elif row.DCA2 == 29002:
                row.Damage_Ag2 = "Sudden Aspen Decline"
                rows.updateRow(row)
            elif row.DCA2 == 50003:
                row.Damage_Ag2 = "Drought"
                rows.updateRow(row)
            elif row.DCA2 == 50013:
                row.Damage_Ag2 = "Wind-tornado/hurricane"
                rows.updateRow(row)
            elif row.DCA2 == 70008:
                row.Damage_Ag2 = "Mechanical"
                rows.updateRow(row)
            elif row.DCA2 == 71001:
                row.Damage_Ag2 = "Woodland cutting"
                rows.updateRow(row)
            elif row.DCA2 == 90000:
                row.Damage_Ag2 = "Unknown"
                rows.updateRow(row)
            elif row.DCA2 == 90009:
                rows.Damage_Ag2 = "Mortality"
                rows.updateRow(row)
            elif row.DCA2 == 99999:
                row.Damage_Ag2 = "No Data"
                rows.updateRow(row)
            else:
                row.Damage_Ag2 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.DCA3 == 11007:
                row.Damage_Ag3 = "Douglas-fir beetle"
                rows.updateRow(row)
            elif row.DCA3 == 11009:
                row.Damage_Ag3 = "Spruce beetle"
                rows.updateRow(row)
            elif row.DCA3 == 11015:
                row.Damage_Ag3 = "Western balsam bark beetle"
                rows.updateRow(row)
            elif row.DCA3 == 11019:
                row.Damage_Ag3 = "Pinyon Ips"
                rows.updateRow(row)
            elif row.DCA3 == 11035:
                row.Damage_Ag3 = "Cedar bark beetles"
                rows.updateRow(row)
            elif row.DCA3 == 11050:
                row.Damage_Ag3 = "Fir engraver"
                rows.updateRow(row)
            elif row.DCA3 == 11900:
                row.Damage_Ag3 = "Unknown bark beetle"
                rows.updateRow(row)
            elif row.DCA3 == 12004:
                row.Damage_Ag3 = "Needleminers"
                rows.updateRow(row)
            elif row.DCA3 == 12005:
                row.Damage_Ag3 = "Sawflies"
                rows.updateRow(row)
            elif row.DCA3 == 12040:
                row.Damage_Ag3 = "Western spruce budworm"
                rows.updateRow(row)
            elif row.DCA3 == 12141:
                row.Damage_Ag3 = "Elm leaf beetle"
                rows.updateRow(row)
            elif row.DCA3 == 12123:
                row.Damage_Ag3 = "Douglas-fir tussock moth"
                rows.updateRow(row)
            elif row.DCA3 == 12239:
                row.Damage_Ag3 = "Tamarisk Leaf Beetles"
                rows.updateRow(row)
            elif row.DCA3 == 12800:
                row.Damage_Ag3 = "Other defoliator"
                rows.updateRow(row)
            elif row.DCA3 == 12900:
                row.Damage_Ag3 = "Unknown defoliator"
                rows.updateRow(row)
            elif row.DCA3 == 14029:
                row.Damage_Ag3 = "Pinyon needle scale"
                rows.updateRow(row)
            elif row.DCA3 == 25005:
                row.Damage_Ag3 = "Needlecast"
                rows.updateRow(row)
            elif row.DCA3 == 29002:
                row.Damage_Ag3 = "Sudden Aspen Decline"
                rows.updateRow(row)
            elif row.DCA3 == 50003:
                row.Damage_Ag3 = "Drought"
                rows.updateRow(row)
            elif row.DCA3 == 50013:
                row.Damage_Ag3 = "Wind-tornado/hurricane"
                rows.updateRow(row)
            elif row.DCA3 == 70008:
                row.Damage_Ag3 = "Mechanical"
                rows.updateRow(row)
            elif row.DCA3 == 71001:
                row.Damage_Ag3 = "Woodland cutting"
                rows.updateRow(row)
            elif row.DCA3 == 90000:
                row.Damage_Ag3 = "Unknown"
                rows.updateRow(row)
            elif row.DCA3 == 90009:
                rows.Damage_Ag3 = "Mortality"
                rows.updateRow(row)
            elif row.DCA3 == 99999:
                row.Damage_Ag3 = "No Data"
                rows.updateRow(row)
            else:
                row.Damage_Ag3 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.HOST1 == -1:
                row.Host_Spec1 = "No Data"
                rows.updateRow(row)
            elif row.HOST1 == 15:
                row.Host_Spec1 = "White Fir"
                rows.updateRow(row)
            elif row.HOST1 == 18:
                row.Host_Spec1 = "Corbark Fir"
                rows.updateRow(row)
            elif row.HOST1 == 57:
                row.Host_Spec1 = "Redcedar; Juniper"
                rows.updateRow(row)
            elif row.HOST1 == 90:
                row.Host_Spec1 = "Spruce Species"
                rows.updateRow(row)
            elif row.HOST1 == 93:
                row.Host_Spec1 = "Engelmann Spruce"
                rows.updateRow(row)
            elif row.HOST1 == 102:
                row.Host_Spec1 = "Bristlecone Pine"
                rows.updateRow(row)
            elif row.HOST1 == 106:
                row.Host_Spec1 = "Common Pinyon"
                rows.updateRow(row)
            elif row.HOST1 == 114:
                row.Host_Spec1 = "Southwestern White Pine"
                rows.updateRow(row)
            elif row.HOST1 == 122:
                row.Host_Spec1 = "Ponderosa Pine"
                rows.updateRow(row)
            elif row.HOST1 == 202:
                row.Host_Spec1 = "Douglas-Fir"
                rows.updateRow(row)
            elif row.HOST1 == 299:
                row.Host_Spec1 = "Unknown Conifer(s)"
                rows.updateRow(row)
            elif row.HOST1 == 740:
                row.Host_Spec1 = "Cottonwood, Poplar"
                rows.updateRow(row)
            elif row.HOST1 == 746:
                row.Host_Spec1 = "Quaking Aspen"
                rows.updateRow(row)
            elif row.HOST1 == 800:
                row.Host_Spec1 = "Oak"
                rows.updateRow(row)
            elif row.HOST1 == 991:
                row.Host_Spec1 = "Saltcedar"
                rows.updateRow(row)
            elif row.HOST1 == 998:
                row.Host_Spec1 = "Not listed"
                rows.updateRow(row)
            elif row.HOST1 == 9998:
                row.Host_Spec1 = "Not listed"
                rows.updateRow(row)
            else:
                row.Host_Spec1 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.HOST2 == -1:
                row.Host_Spec2 = "No Data"
                rows.updateRow(row)
            elif row.HOST2 == 15:
                row.Host_Spec2 = "White Fir"
                rows.updateRow(row)
            elif row.HOST2 == 18:
                row.Host_Spec2 = "Corbark Fir"
                rows.updateRow(row)
            elif row.HOST2 == 57:
                row.Host_Spec2 = "Redcedar; Juniper"
                rows.updateRow(row)
            elif row.HOST2 == 90:
                row.Host_Spec2 = "Spruce Species"
                rows.updateRow(row)
            elif row.HOST2 == 93:
                row.Host_Spec2 = "Engelmann Spruce"
                rows.updateRow(row)
            elif row.HOST2 == 102:
                row.Host_Spec2 = "Bristlecone Pine"
                rows.updateRow(row)
            elif row.HOST2 == 106:
                row.Host_Spec2 = "Common Pinyon"
                rows.updateRow(row)
            elif row.HOST2 == 114:
                row.Host_Spec2 = "Southwestern White Pine"
                rows.updateRow(row)
            elif row.HOST2 == 122:
                row.Host_Spec2 = "Ponderosa Pine"
                rows.updateRow(row)
            elif row.HOST2 == 202:
                row.Host_Spec2 = "Douglas-Fir"
                rows.updateRow(row)
            elif row.HOST2 == 299:
                row.Host_Spec2 = "Unknown Conifer(s)"
                rows.updateRow(row)
            elif row.HOST2 == 740:
                row.Host_Spec2 = "Cottonwood, Poplar"
                rows.updateRow(row)
            elif row.HOST2 == 746:
                row.Host_Spec2 = "Quaking Aspen"
                rows.updateRow(row)
            elif row.HOST2 == 800:
                row.Host_Spec2 = "Oak"
                rows.updateRow(row)
            elif row.HOST2 == 991:
                row.Host_Spec2 = "Saltcedar"
                rows.updateRow(row)
            elif row.HOST2 == 998:
                row.Host_Spec2 = "Not listed"
                rows.updateRow(row)
            elif row.HOST2 == 9998:
                row.Host_Spec2 = "Not listed"
                rows.updateRow(row)
            else:
                row.Host_Spec2 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.HOST3 == -1:
                row.Host_Spec3 = "No Data"
                rows.updateRow(row)
            elif row.HOST3 == 15:
                row.Host_Spec3 = "White Fir"
                rows.updateRow(row)
            elif row.HOST3 == 18:
                row.Host_Spec3 = "Corbark Fir"
                rows.updateRow(row)
            elif row.HOST3 == 57:
                row.Host_Spec3 = "Redcedar; Juniper"
                rows.updateRow(row)
            elif row.HOST3 == 90:
                row.Host_Spec3 = "Spruce Species"
                rows.updateRow(row)
            elif row.HOST3 == 93:
                row.Host_Spec3 = "Engelmann Spruce"
                rows.updateRow(row)
            elif row.HOST3 == 102:
                row.Host_Spec3 = "Bristlecone Pine"
                rows.updateRow(row)
            elif row.HOST3 == 106:
                row.Host_Spec3 = "Common Pinyon"
                rows.updateRow(row)
            elif row.HOST3 == 114:
                row.Host_Spec3 = "Southwestern White Pine"
                rows.updateRow(row)
            elif row.HOST3 == 122:
                row.Host_Spec3 = "Ponderosa Pine"
                rows.updateRow(row)
            elif row.HOST3 == 202:
                row.Host_Spec3 = "Douglas-Fir"
                rows.updateRow(row)
            elif row.HOST3 == 299:
                row.Host_Spec3 = "Unknown Conifer(s)"
                rows.updateRow(row)
            elif row.HOST3 == 740:
                row.Host_Spec3 = "Cottonwood, Poplar"
                rows.updateRow(row)
            elif row.HOST3 == 746:
                row.Host_Spec3 = "Quaking Aspen"
                rows.updateRow(row)
            elif row.HOST3 == 800:
                row.Host_Spec3 = "Oak"
                rows.updateRow(row)
            elif row.HOST3 == 991:
                row.Host_Spec3 = "Saltcedar"
                rows.updateRow(row)
            elif row.HOST3 == 998:
                row.Host_Spec3 = "Not listed"
                rows.updateRow(row)
            elif row.HOST3 == 9998:
                row.Host_Spec3 = "Not listed"
                rows.updateRow(row)
            else:
                row.Host_Spec3 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.FOR_TYPE1 == -1:
                row.Frst_Type1 = "No Data"
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 3000:
                row.Frst_Type1 = "Western Fir-Spruce"
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 6740:
                row.Frst_Type1 = "Cottonwood"
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 6746:
                row.Frst_Type1 = "Quaking Aspen"
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 7141:
                row.Frst_Type1 = "Pinyon-Juniper"
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 9000:
                row.Frst_Type1 = "Mixed Conifers"
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 9301:
                row.Frst_Type1 = "ABCO, PSME, PIEN"                             # Douglas-fir, Engelmann spruce, white fir
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 9305:
                row.Frst_Type1 = "CUAR, JUDE, JUMO, JUSC, JUOS"                 # Alligator juniper, Arizona cypress, oneseed juniper, Rocky Mountain juniper, Utah juniper
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 9311:
                row.Frst_Type1 = "ABCO, PSME, ABLAA, PIEN"                      # corkbark fir, Douglas-fir, Engelmann spruce, white fir
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 9315:
                row.Frst_Type1 = "POFR2, POAN3"                                 # Fremont cottonwood, narrowleaf cottonwood
                rows.updateRow(row)
            elif row.FOR_TYPE1 == 9316:
                row.Frst_Type1 = "QUAR, QUGA, QUOB, GUGR3"                      # Arizona white oak, gambel oak, gray oak, Mexican blue oak
                rows.updateRow(row)
            else:
                row.Frst_Type1 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.FOR_TYPE2 == -1:
                row.Frst_Type2 = "No Data"
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 3000:
                row.Frst_Type2 = "Western Fir-Spruce"
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 6740:
                row.Frst_Type2 = "Cottonwood"
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 6746:
                row.Frst_Type2 = "Quaking Aspen"
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 7141:
                row.Frst_Type2 = "Pinyon-Juniper"
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 9000:
                row.Frst_Type2 = "Mixed Conifers"
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 9301:
                row.Frst_Type2 = "ABCO, PSME, PIEN"                             # Douglas-fir, Engelmann spruce, white fir
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 9305:
                row.Frst_Type2 = "CUAR, JUDE, JUMO, JUSC, JUOS"                 # Alligator juniper, Arizona cypress, oneseed juniper, Rocky Mountain juniper, Utah juniper
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 9311:
                row.Frst_Type2 = "ABCO, PSME, ABLAA, PIEN"                      # corkbark fir, Douglas-fir, Engelmann spruce, white fir
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 9315:
                row.Frst_Type2 = "POFR2, POAN3"                                 # Fremont cottonwood, narrowleaf cottonwood
                rows.updateRow(row)
            elif row.FOR_TYPE2 == 9316:
                row.Frst_Type2 = "QUAR, QUGA, QUOB, GUGR3"                      # Arizona white oak, gambel oak, gray oak, Mexican blue oak
                rows.updateRow(row)
            else:
                row.Frst_Type2 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.FOR_TYPE3 == -1:
                row.Frst_Type3 = "No Data"
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 3000:
                row.Frst_Type3 = "Western Fir-Spruce"
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 6740:
                row.Frst_Type3 = "Cottonwood"
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 6746:
                row.Frst_Type3 = "Quaking Aspen"
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 7141:
                row.Frst_Type3 = "Pinyon-Juniper"
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 9000:
                row.Frst_Type3 = "Mixed Conifers"
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 9301:
                row.Frst_Type3 = "ABCO, PSME, PIEN"                             # Douglas-fir, Engelmann spruce, white fir
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 9305:
                row.Frst_Type3 = "CUAR, JUDE, JUMO, JUSC, JUOS"                 # Alligator juniper, Arizona cypress, oneseed juniper, Rocky Mountain juniper, Utah juniper
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 9311:
                row.Frst_Type3 = "ABCO, PSME, ABLAA, PIEN"                      # corkbark fir, Douglas-fir, Engelmann spruce, white fir
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 9315:
                row.Frst_Type3 = "POFR2, POAN3"                                 # Fremont cottonwood, narrowleaf cottonwood
                rows.updateRow(row)
            elif row.FOR_TYPE3 == 9316:
                row.Frst_Type3 = "QUAR, QUGA, QUOB, GUGR3"                      # Arizona white oak, gambel oak, gray oak, Mexican blue oak
                rows.updateRow(row)
            else:
                row.Frst_Type3 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.PCT_MORT1 == -1:
                row.Pcnt_Mort1 = "No Data"
                rows.updateRow(row)
            elif row.PCT_MORT1 == 1:
                row.Pcnt_Mort1 = "Very Light (1-3%)"
                rows.updateRow(row)
            elif row.PCT_MORT1 == 2:
                row.Pcnt_Mort1 = "Light (4-10%)"
                rows.updateRow(row)
            elif row.PCT_MORT1 == 3:
                row.Pcnt_Mort1 = "Moderate (11-29%)"
                rows.updateRow(row)
            elif row.PCT_MORT1 == 4:
                row.Pcnt_Mort1 = "Severe (30-50%)"
                rows.updateRow(row)
            elif row.PCT_MORT1 == 5:
                row.Pcnt_Mort1 = "Very severe (>50%)"
                rows.updateRow(row)
            else:
                row.Pcnt_Mort1 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.PCT_MORT2 == -1:
                row.Pcnt_Mort2 = "No Data"
                rows.updateRow(row)
            elif row.PCT_MORT2 == 1:
                row.Pcnt_Mort2 = "Very Light (1-3%)"
                rows.updateRow(row)
            elif row.PCT_MORT2 == 2:
                row.Pcnt_Mort2 = "Light (4-10%)"
                rows.updateRow(row)
            elif row.PCT_MORT2 == 3:
                row.Pcnt_Mort2 = "Moderate (11-29%)"
                rows.updateRow(row)
            elif row.PCT_MORT2 == 4:
                row.Pcnt_Mort2 = "Severe (30-50%)"
                rows.updateRow(row)
            elif row.PCT_MORT2 == 5:
                row.Pcnt_Mort2 = "Very severe (>50%)"
                rows.updateRow(row)
            else:
                row.Pcnt_Mort2 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.PCT_MORT3 == -1:
                row.Pcnt_Mort3 = "No Data"
                rows.updateRow(row)
            elif row.PCT_MORT3 == 1:
                row.Pcnt_Mort3 = "Very Light (1-3%)"
                rows.updateRow(row)
            elif row.PCT_MORT3 == 2:
                row.Pcnt_Mort3 = "Light (4-10%)"
                rows.updateRow(row)
            elif row.PCT_MORT3 == 3:
                row.Pcnt_Mort3 = "Moderate (11-29%)"
                rows.updateRow(row)
            elif row.PCT_MORT3 == 4:
                row.Pcnt_Mort3 = "Severe (30-50%)"
                rows.updateRow(row)
            elif row.PCT_MORT3 == 5:
                row.Pcnt_Mort3 = "Very severe (>50%)"
                rows.updateRow(row)
            else:
                row.Pcnt_Mort3 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.DMG_TYPE1 == -1:
                row.Dmg_Typ1 = "No Data"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 1:
                row.Dmg_Typ1 = "Defoliation"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 2:
                row.Dmg_Typ1 = "Mortality"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 3:
                row.Dmg_Typ1 = "Discoloration"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 4:
                row.Dmg_Typ1 = "Dieback"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 5:
                row.Dmg_Typ1 = "Topkill"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 6:
                row.Dmg_Typ1 = "Branch breakage"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 7:
                row.Dmg_Typ1 = "Main stem broken/uprooted"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 8:
                row.Dmg_Typ1 = "Branch flagging"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 9:
                row.Dmg_Typ1 = "No damage"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 10:
                row.Dmg_Typ1 = "Other damage"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 11:
                row.Dmg_Typ1 = "Previously undocumented (old) mortality"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 12:
                row.Dmg_Typ1 = "Defoliation - Light (<50% of foliage)"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 13:
                row.Dmg_Typ1 = "Defoliation - Moderate (50-75% foliage)"
                rows.updateRow(row)
            elif row.DMG_TYPE1 == 14:
                row.Dmg_Typ1 = "Defoliation - Heavy (>75% of foliage)"
                rows.updateRow(row)
            else:
                row.Dmg_Typ1 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.DMG_TYPE2 == -1:
                row.Dmg_Typ2 = "No Data"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 1:
                row.Dmg_Typ2 = "Defoliation"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 2:
                row.Dmg_Typ2 = "Mortality"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 3:
                row.Dmg_Typ2 = "Discoloration"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 4:
                row.Dmg_Typ2 = "Dieback"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 5:
                row.Dmg_Typ2 = "Topkill"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 6:
                row.Dmg_Typ2 = "Branch breakage"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 7:
                row.Dmg_Typ2 = "Main stem broken/uprooted"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 8:
                row.Dmg_Typ2 = "Branch flagging"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 9:
                row.Dmg_Typ2 = "No damage"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 10:
                row.Dmg_Typ2 = "Other damage"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 11:
                row.Dmg_Typ2 = "Previously undocumented (old) mortality"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 12:
                row.Dmg_Typ2 = "Defoliation - Light (<50% of foliage)"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 13:
                row.Dmg_Typ2 = "Defoliation - Moderate (50-75% foliage)"
                rows.updateRow(row)
            elif row.DMG_TYPE2 == 14:
                row.Dmg_Typ2 = "Defoliation - Heavy (>75% of foliage)"
                rows.updateRow(row)
            else:
                row.Dmg_Typ2 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.DMG_TYPE3 == -1:
                row.Dmg_Typ3 = "No Data"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 1:
                row.Dmg_Typ3 = "Defoliation"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 2:
                row.Dmg_Typ3 = "Mortality"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 3:
                row.Dmg_Typ3 = "Discoloration"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 4:
                row.Dmg_Typ3 = "Dieback"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 5:
                row.Dmg_Typ3 = "Topkill"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 6:
                row.Dmg_Typ3 = "Branch breakage"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 7:
                row.Dmg_Typ3 = "Main stem broken/uprooted"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 8:
                row.Dmg_Typ3 = "Branch flagging"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 9:
                row.Dmg_Typ3 = "No damage"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 10:
                row.Dmg_Typ3 = "Other damage"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 11:
                row.Dmg_Typ3 = "Previously undocumented (old) mortality"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 12:
                row.Dmg_Typ3 = "Defoliation - Light (<50% of foliage)"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 13:
                row.Dmg_Typ3 = "Defoliation - Moderate (50-75% foliage)"
                rows.updateRow(row)
            elif row.DMG_TYPE3 == 14:
                row.Dmg_Typ3 = "Defoliation - Heavy (>75% of foliage)"
                rows.updateRow(row)
            else:
                row.Dmg_Typ3 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.SEVERITY1 == -1:
                row.Svrty_1 = "No Data"
                rows.updateRow(row)
            elif row.SEVERITY1 == 1:
                row.Svrty_1 = "Low (Equal to or less than 50% defoliation)"
                rows.updateRow(row)
            elif row.SEVERITY1 == 2:
                row.Svrty_1 = "High (More than 50% defoliation)"
                rows.updateRow(row)
            else:
                row.Svrty_1 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.SEVERITY2 == -1:
                row.Svrty_2 = "No Data"
                rows.updateRow(row)
            elif row.SEVERITY2 == 1:
                row.Svrty_2 = "Low (Equal to or less than 50% defoliation)"
                rows.updateRow(row)
            elif row.SEVERITY2 == 2:
                row.Svrty_2 = "High (More than 50% defoliation)"
                rows.updateRow(row)
            else:
                row.Svrty_2 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows

        rows = arcpy.UpdateCursor(shape)
        for row in rows:
            if row.SEVERITY3 == -1:
                row.Svrty_3 = "No Data"
                rows.updateRow(row)
            elif row.SEVERITY3 == 1:
                row.Svrty_3 = "Low (Equal to or less than 50% defoliation)"
                rows.updateRow(row)
            elif row.SEVERITY3 == 2:
                row.Svrty_3 = "High (More than 50% defoliation)"
                rows.updateRow(row)
            else:
                row.Svrty_3 = "Script Failed"
                rows.updateRow(row)
        del row
        del rows
        return

class MapScale(object):
    def __init__(self):
        self.label = "Map Scale - Convert Inches to Miles"
        self.description = "This tool performs a simple conversion converting inches to miles. This could be useful if you include a map scale on your map (displayed in ArcMap on the 'Standard Toolbar' located below the top \
        menu text, 'Selection', 'Geoprocessing', and 'Customize'). For instance, if the map scale were 1:150,000 an interpretation using inches would be that 1 inch on the map equals 150,000 inches on the ground (real life).\
        Since this is a difficult value to comprehend, converting the value to miles provides one with an easier comprehension. On the map, you could include 'Scale 1:150,000  1 inch = 2.37 miles', while including the number of \
        significant digits you deem necessary.  The tool is easy to use: enter a value in the first field, and the 2nd field is automatically populated with the value in miles. Running the tool (clicking OK) isn't even \
        necessary to make the conversion. If you do press OK, a message after the tool runs will state the scale and what 1 inch equals so long as 'Details' are shown in the tool run popup box.\
        *IMPORTANT* The size of the map template (e.g. ANSI A, 8.5'' x 11.0'' aka. standard letter size), determines what size you should print your PDF map. If you printed a map at a different template size (print a map created using ANSI A at say ANSI B \
        or vice versa, the interpretation of the map scale will be incorrect (one inch on the digital copy won't correspond to one inch on the paper copy). Therefore, if you plan to include a map scale, be sure to print it on paper\
        that reflects the size of the template."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Inches",
            name = "Inches",
            datatype = "GPDouble",
            parameterType = "Required",
            direction = "Input")
        param1 = arcpy.Parameter(
            displayName = "Miles",
            name = "Miles",
            datatype = "GPDouble",
            parameterType = "Required",
            direction = "Input")

        params = [param0, param1]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[0].altered:
            inches = parameters[0].value
            feet = inches/12
            miles = feet/5280
            parameters[1].value = miles
        else:
            pass
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        inches = parameters[0].value
        feet = inches/12
        miles = feet/5280
        arcpy.AddMessage("Map Scale 1:{0}          1 inch = {1} miles".format(inches, miles))
        return

class OARS_Shapefile_Developer(object):
    def __init__(self):
        self.label = "OARS Shapefile Developer"
        self.description = "This tool fills in a shapefile's attributes with user-selected and user-typed input. Note that this " \
        "tool does not actually upload the shapefile to OARS - that must be done separately by you after running the tool. What this tool " \
        "provides is a convenient & quick method to enter required data into the attribute table while providing data integrity checks. This " \
        "standardization increases the value of the geospatial data collected and subsequently reported to OARS. The tool allows each user " \
        "to name the shapefile whatever they like, so if you have developed your own naming convention to keep track of shapefiles, feel " \
        "free to use it. Any special characters, that is, values that aren't the alphabet (a-zA-Z), numbers (0-9), or underscore (_), will " \
        "automatically be removed by the tool because special characters violate ESRI's naming conventions. In contrast, special characters are " \
        "acceptable in a shapefile's attribute table."
        self.canRunInBackground = False
        self.category = "OARS"

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Input Polygon",
            name = "Input Polygon",
            datatype = ["DEFeatureClass", "DEShapefile", "DEFile", "GPFeatureLayer"],             # Set both Feature class, shapefile, and KML/KMZ files  ("DEFILE" will allow KML/KMZ files).
            parameterType = "Required",
            direction = "Input")
        param1 = arcpy.Parameter(
            displayName = "District",
            name = "District",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param1.filter.type = "ValueList"
        param1.filter.list = ['N1S - Chama', 'N2S - Cimarron', 'N3S - Socorro', 'N4S - Las Vegas', 'N5S - Capitan', 'N6S - Bernalillo', 'N7S - Inmate Work Camp', 'N8S - Forest and Watershed Health', 'N9S - Santa Fe']
        param2 = arcpy.Parameter(
            displayName = "Workplan Number",
            name = "Workplan Number",
            datatype = "GPLong",
            parameterType = "Required",
            direction = "Input")
        param3 = arcpy.Parameter(
            displayName = "Fund Number / Cost Center",
            name = "Fund Number / Cost Center",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param4 = arcpy.Parameter(
            displayName = "Cooperator ID",
            name = "Cooperator ID",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param5 = arcpy.Parameter(
            displayName = "Land Ownership",
            name = "Land Ownership",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = "True")
        param5.filter.type = "ValueList"
        param5.filter.list = ['Private Landowner', 'Bureau of Land Management', 'Bureau of Reclamation', 'Department of Defense', 'Department of Energy', \
        'US Fish and Wildlife Service', 'US Forest Service', 'Municipality', 'National Park Service', 'NM Department of Game & Fish', 'NM Department of Transportation', 'NM State Forestry', 'NM State Land Office', 'NM State Parks', 'Natural Resources Conservation Service', 'Tribal/Pueblo']
        param6 = arcpy.Parameter(
            displayName = "Agencies Involved",
            name = "Agencies Involved",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = "True")
        param6.filter.type = "ValueList"
        param6.filter.list = ['NM State Forestry', 'Bureau of Indian Affairs', 'Bureau of Land Management', 'Bureau of Reclamation', 'County', 'Department of Defense', 'Department of Energy', \
        'US Fish and Wildlife Service', 'US Forest Service', 'Municipality', 'National Park Service', 'NM Department of Game & Fish', 'NM Department of Transportation', 'NM State Land Office', 'NM State Parks', 'Natural Resources Conservation Service', 'Soil and Water Conservation District']
        param6.value = "NM State Forestry"                                      # Set Default value
        param7 = arcpy.Parameter(
            displayName = "Grant Title",
            name = "Grant Title",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param8 = arcpy.Parameter(
            displayName = "Project Name",
            name = "Project Name",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param9 = arcpy.Parameter(
            displayName = "Community Wildfire Protection Plan (CWPP) by County",
            name = "Community Wildfire Protection Plan (CWPP)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param9.filter.type = "ValueList"
        param9.filter.list = ['Bernalillo', 'Catron', 'Chaves', 'Cibola', 'Colfax', 'Curry', 'De Baca', 'Dona Ana', 'Eddy', 'Grant', 'Guadalupe', 'Harding', 'Hidalgo', 'Lea', 'Lincoln', \
        'Los Alamos', 'Luna', 'McKinley', 'Mora', 'Otero', 'Quay', 'Rio Arriba', 'Roosevelt', 'San Juan', 'San Miguel', 'Sandoval', 'Santa Fe', 'Sierra', 'Socorro', 'Taos', 'Torrance', 'Union', 'Valencia']
        param10 = arcpy.Parameter(
            displayName = "Communities at Risk (CAR)",
            name = "Communities at Risk (CAR)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = "True")
        param10.filter.type = "ValueList"
        param11 = arcpy.Parameter(
            displayName = "Did you have any Communities at Risk that weren't available as options in this tool?",
            name = "Need_fields_that_aren't_available",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")
        param12 = arcpy.Parameter(
            displayName = "Forest Type",
            name = "Forest Type",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = "True")
        param12.filter.type = "ValueList"
        param12.filter.list = ['Aspen', 'Blue spruce', 'Bosque', 'Deciduous oak', 'Douglas-fir', 'Engelmann spruce', 'Evergreen oak', \
        'Juniper', 'Mixed Conifer', 'Pinyon-Juniper', 'Ponderosa pine', 'Riparian', 'Spruce-fir', 'White fir']
        param13 = arcpy.Parameter(
            displayName = "Treatment",
            name = "Treatment",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = "True")
        param13.filter.type = "ValueList"
        param13.filter.list = ['Chipping', 'Forest Health Thinning', 'Forest Stand Improvement', 'Fuel Break', 'Lop and Scatter', 'Hazardous Fuel Reduction Around Community at Risk', \
        'Maintenance', 'Mastication', 'Prescribed Burn', 'Stump and Spray', 'Tree Felling and Removal']
        param14 = arcpy.Parameter(
            displayName = "Accomplishment Date",
            name = "Accomplishment Date",
            datatype = "GPDate",
            parameterType = "Required",
            direction = "Input")
        param15 = arcpy.Parameter(
            displayName = "Fiscal Year",
            name = "Fiscal Year",
            datatype = "GPLong",
            parameterType = "Required",
            direction = "Input")
        param15.filter.type = "ValueList"
        year = now.year
        month = now.month
        param15.filter.list = range(now.year - 1, now.year + 2)
        if month in (1, 2, 3, 4, 5, 6):
            param15.value = year
        else:
            param15.value = year + 1
        param16 = arcpy.Parameter(
            displayName = "Name your Shapefile",
            name = "Name your Shapefile",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param17 = arcpy.Parameter(
            displayName = "Choose Folder on Local Drive to Save your Shapefile ",
            name = "Choose Folder on Local Drive to Save your Shapefile",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input")
        param17.filter.list = ["Workspace"]                                     # Set filter to only accept a folder. This just makes dialog box display workspace
        param18 = arcpy.Parameter(
            displayName = "Do you want to add the formatted OARS Shapefile to your current MXD?",
            name = "Add_OARS_Shapefile_to_Map?",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")
        param19 = arcpy.Parameter(
            displayName = "Do you want to create a KMZ file too?",
            name = "Do you want to create a KMZ file too?",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")
        params = [param0, param1, param2, param3, param4, param5, param6, param7, param8, param9, param10, param11, param12, param13, param14, param15, param16, param17, param18, param19]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[9].value == "Bernalillo":
            parameters[10].filter.list = ['Albuquerque', 'Alley Place', 'Barton', 'Canoncito', 'Canyon Estates', 'Carnuel', 'Casa Loma', 'Cedar Crest', 'Cedro', 'Chilili Land Grant', 'Dennis Chavez Estates', 'El Refugio', 'El Tablazon', 'Escabosa', 'Forest Park', 'Frost (historical)', 'Juan Tomaas', 'Los Pinos', 'Los Ranchos de Albuquerque', 'Miera', 'Ponderosa', 'Ponderosa Pine', 'Primera Agua', 'Rincon', 'San Antonio', 'San Antonito', 'Sandia Knolls', 'Sandia Park', 'Sedillo', 'Tijeras', 'Yrisarri', 'Zamora']
        elif parameters[9].value == "Catron":
            parameters[10].filter.list = ['Apache Creek', 'Aragon', 'Coyote Creek', 'Cruzville', 'Datil Area', 'Davenport', 'Elk Springs', 'Glenwood', 'Horse Mountain', 'Jewett Gap', 'Luna', 'Mogollon', 'Pie Town', 'Quemado Lake Estates', 'Rancho Grande Estates', 'Reserve', 'Wildhorse', 'Willow Creek']
        elif parameters[9].value == "Chaves":
            parameters[10].filter.list = ['Country Club', 'Dexter', 'District 8', 'Dunken', 'Dunken / Penasco School', 'East Grand Plains', 'Hagerman', 'Lake Arthur', 'Lake Van', 'Midway', 'Penasco 1 FD', 'Penasco 2 FD', 'Penasco Valley', 'Rio Felix FD', 'Roswell, East', 'Roswell, North', 'Roswell, Northeast', 'Roswell, Northwest', 'Roswell, South', 'Roswell, Southwest', 'Roswell, West', 'South Spring Acres', 'Tierra Grande']
        elif parameters[9].value == "Cibola":
            parameters[10].filter.list = ['Bluewater', 'Bluewater Acres', 'Candy Kitchen', 'Crestview / Twin Buttes / Crested Butte', 'El Morro', 'Lobo Canyon', 'Milan', 'San Mateo']
        elif parameters[9].value == "Colfax":
            parameters[10].filter.list = ['Abbott', 'Agua Fria', 'Angel Fire', 'Bartlett', 'Black Lake / Black Lake Resort', 'Carisbrooke', 'Cimarron', 'Colfax', 'Eagle Nest', 'Elizabethtown', 'Elk Ridge', 'Farley', 'Gardiner', 'Hidden Lake', 'Idlewild', 'Lakeview Pines', 'Linwood', 'Maxwell', 'Miami', 'NM Boys School', 'Philmont HQ', 'Pine Forest Estates', 'Raton', 'Rayado', 'Springer', 'Sugarite', 'Sugarite Canyon State Park', 'Taos Pines', 'Taylor Springs', 'Tinaja', 'Ute Park', 'Vermejo Park Ranch Headquarters', 'Whittington Center', 'Yankee']
        elif parameters[9].value == "Curry":
            parameters[10].filter.list = ['Bellview', 'Broadview', 'Clovis', 'Clovis Industrial Park', 'Grady', 'Hachita Hills', 'Jack Rabbit Run', 'Melrose', 'Sun Ridge Estates', 'Turquoise Estates', 'Vans Acres']
        elif parameters[9].value == "De Baca":
            parameters[10].filter.list = ['Fort Sumner', 'Lake Sumner', 'Sunnyside (Old Town)', 'Taiban', 'Valley', 'Yeso']
        elif parameters[9].value == "Dona Ana":
            parameters[10].filter.list = ['Chaparral', 'Dona Ana', 'Dripping Springs', 'Fairacres', 'Garfield', 'Hatch', 'Las Alturas (Talavera)', 'Mesilla', 'Radium Springs', 'Rincon', 'Vado - La Mesa']
        elif parameters[9].value == "Eddy":
            parameters[10].filter.list = ['Artesia', 'Atoka', 'Carlsbad', 'Carlsbad Caverns', 'Cottonwood', 'Happy Valley', 'Hope', 'Joel', 'La Huerta', 'Loco Hills', 'Loving', 'Malaga', 'Otis', 'Queen', 'Riverside', 'Waste Isolation Pilot Plant', 'White\'s City']
        elif parameters[9].value == "Grant":
            parameters[10].filter.list = ['Bayard', 'Buckhorn', 'Burro Mountain', 'Chisholm Ranch Subdivision', 'Cliff', 'Cottage San', 'Cullum Estates Subdivision', 'East Peterson / West Race Track', 'East Racetrack / Santa Clara', 'Faywood', 'Feeley', 'Flying A Subdivision', 'Gila', 'Gila Hot Springs', 'Hanover', 'Hatchita Town Site', 'HWY 9,146, & 81', 'I-10 Corridor', 'Lake Roberts', 'Lake Roberts Heights', 'LS Mesa', 'Mangus Springs', 'Mangus Terrace', 'Mimbres Valley', 'Mule Creek', 'North Swan and Dos Griegos', 'Oak Grove', 'Old Arenas Valley Rd', 'Owens', 'Paradise Acres I', 'Paradise Acres II', 'Pine Cienega', 'Pinos Altos', 'Pinos Altos Mountin Estates', 'River Glen', 'Riverside', 'Rosedale / West Peterson', 'San Juan', 'San Lorenzo', 'Santa Clara', 'Silver City', 'Sunrise Estates', 'Table Butte', 'Trout Valley', 'Truck Bypass Rd / American & Peaceful Valley Mobile Home Park', 'Tyrone Town Site', 'Viva Santa Rita', 'Wagon Wheel', 'White Signal', 'Wind Canyon']
        elif parameters[9].value == "Guadalupe":
            parameters[10].filter.list = ['Anton Chico', 'Colonias', 'Milagro', 'Newkirk / Cuervo', 'Pastura', 'Pintada', 'Puerto De Luna', 'Santa Rosa', 'Vaughn']
        elif parameters[9].value == "Harding":
            parameters[10].filter.list = ['Mosquero', 'Roy', 'Solano']
        elif parameters[9].value == "Hidalgo":
            parameters[10].filter.list = ['Animas', 'Antelope Wells & Port of Entry', 'Big Hatchet Peak', 'Cotton City', 'Gila Neblett Valley', 'Gillespie Mountain', 'I-10 Corridor', 'Playas', 'Rodeo', 'Rodeo Rancho Ceilo', 'Shakespeare', 'Steins', 'Virden']
        elif parameters[9].value == "Lea":
            parameters[10].filter.list = ['Eunice', 'Hobbs', 'Jal', 'Knowles', 'Lovington', 'Maljamar', 'Monument', 'Tatum']
        elif parameters[9].value == "Lincoln":
            parameters[10].filter.list = ['Alto', 'Ancho', 'Angus', 'Arabela', 'Bonito', 'Capitan', 'Carrizo Canyon', 'Carrizozo', 'Cedar Creek - Alpine Village', 'Copper Ridge', 'Copper Ridge II', 'Corona', 'Eagle Creek', 'Eagle Creek II', 'Enchanted Forest', 'Fawn Ridge', 'Fort Stanton', 'Gavilan Canyon', 'Glencoe', 'Hondo / Tinnie', 'Lincoln', 'Loma Grande', 'Nogal', 'Outlaw', 'Rainmakers', 'Ranches of Ruidoso', 'Ranches of Sonterra', 'Ruidoso', 'Ruidoso Downs', 'Sierra Vista', 'Sun Valley - Sierra Vista', 'Villa Madonna', 'White Oaks']
        elif parameters[9].value == "Los Alamos":
            parameters[10].filter.list = ['Los Alamos', 'White Rock']
        elif parameters[9].value == "Luna":
            parameters[10].filter.list = ['Chance City (historical)', 'Columbus', 'Cookes Peak', 'Dairy Farms', 'El Paso Natural Gas Monitoring Station', 'Florida Mountains', 'Florida Mountains Comm. Site', 'Highway 11', 'Highway 180 and Railroad', 'Highway 26', 'Highway 9 East', 'Highway 9 West', 'I-10 and Railroad', 'International Border Fence', 'Johnson Peak Comm. Site', 'Nutt and Communication Site', 'Rattlesnake Lane', 'Red Mountain', 'Savoy and El Paso Gas Plant', 'Sunshine (historical)', 'Victorio Peak Comm. Site']
        elif parameters[9].value == "McKinley":
            parameters[10].filter.list = ['Black Rock', 'Black Rock / Vanderwagon Corridor', 'Bluewater Lake', 'Chi Chil Tah', 'Church Rock', 'Continental Divide (Thoreau area)', 'Cousins Trading Post', 'Crownpoint', 'Fort Wingate', 'Gallup, Juniper Hills', 'Gamerco', 'Gamerco - Twin Lakes Corridor', 'Iyanbito', 'Manuelito Area', 'Mariano Lake', 'McGaffey', 'McGaffey Lake - Tampico Springs', 'Mentmore Area', 'Mexican Springs', 'Nahodishgish', 'Navajo', 'Navajo Estates (Yah-Ta-Hey-Tse Bonio Corridor)', 'Pinedale - Mariano Lake', 'Pinehaven', 'Prewitt', 'Pueblo Pintado Area', 'Ramah', 'Ramah - Black Rock Corridor', 'Rehoboth', 'Sagar Estates', 'South Navajo - Highway 12 Corridor', 'Thoreau', 'Timberlake', 'Timberlake - Box S Ranch', 'Tse-Yah-Tow', 'Vanderwagen - Sagar Estates', 'Whispering Cedars', 'Yah-ta-hey', 'Zuni (Highway 53 SW Corridor)', 'Zuni Pueblo WUI - Black Rock']
        elif parameters[9].value == "Mora":
            parameters[10].filter.list = ['Chacon', 'Cleveland', 'Gascon', 'Guadalupita', 'Holman', 'La Cueva', 'Ledoux', 'Mora', 'Ocate', 'Ojo Felix', 'Rainsville']
        elif parameters[9].value == "Otero":
            parameters[10].filter.list = ['Bent', 'Cloudcroft', 'Cox Canyon', 'Dry Canyon', 'High Rolls', 'James Canyon', 'Mayhill', 'Mescalero', 'Sacramento', 'Sixteen Springs', 'Sunspot Observatory', 'Timberon', 'Weed']
        elif parameters[9].value == "Quay":
            parameters[10].filter.list = ['Bard', 'Endee', 'Endee Truckstop', 'Forrest', 'Glenrio', 'House', 'Ima', 'Jordan', 'Lesbia', 'Logan', 'McAlister', 'Montoya', 'Nara Visa', 'Pajarito', 'Plaza Largo', 'Porter', 'Quay', 'San Jon', 'Tucumcari', 'Ute Lake Ranch', 'Ute Lake State Park']
        elif parameters[9].value == "Rio Arriba":
            parameters[10].filter.list = ['Alcade', 'Biggs (historical)', 'Brazos', 'Brazos Canyon', 'Buckman Road', 'Canjilon', 'Canones (Abiquiu)', 'Canones (Chama)', 'Cebolla', 'Chama', 'Chama West', 'Chamita', 'Chili', 'Coyote', 'Cumbres & Toitec Scenic Raildroad', 'Diamente (historical)', 'Embudo', 'Ensenada', 'Espanola', 'Fairview', 'Fort Heron', 'Gallina', 'Hernandez', 'La Mesilla', 'La Puente', 'Laguna Vista Estates', 'Los Luceros', 'Los Ojos', 'Lumberton', 'Lyden', 'Ojo Sarco', 'Pinon Ridge', 'Plaza Blanca', 'Ponderosa Estates', 'Rutheron', 'San Juan Pueblo', 'Santa Clara Pueblo', 'Tierra Amarilla', 'Velarde', 'Youngsville']
        elif parameters[9].value == "Roosevelt":
            parameters[10].filter.list = ['Arch', 'Causey', 'Dora', 'Elida', 'Floyd', 'Kenna', 'Milnesand', 'Pep', 'Portales', 'Rogers', 'Tolar']
        elif parameters[9].value == "San Juan":
            parameters[10].filter.list = ['Aztec', 'Blanco', 'Bloomfield', 'Center Point - Cedar Hill', 'Farmington', 'Flora Vista', 'Fruitland - Kirtland', 'La Plata', 'Navajo Dam']
        elif parameters[9].value == "San Miguel":
            parameters[10].filter.list = ['Bernal / Tecolote / Lagunita', 'Bull Creek', 'Colonias (Upper / Lower)', 'Conchas Lake', 'Cowles', 'Dalton Canyon', 'El Porvenir', 'Gallinas', 'Gonzales Ranch', 'Grass Mountain Summer Home Area', 'Hidden Valley', 'Highway 84', 'Las Vegas, North and West', 'Las Vegas, Southeast', 'Lower Pecos Canyon', 'Mineral Hill', 'Montezuma', 'Pecos / East Pecos', 'Pendaries Village', 'Rociada', 'Romeroville / Ojitos Frios', 'Sabinoso', 'San Ignacio / Las Tusas', 'Sapello / Tierra Monte', 'Tecolotito', 'Tererro', 'Trementina - Variadero', 'Tres Lagunas', 'Trujillo', 'Upper Gallinas', 'Villanueva / Pecos River Valley', 'Windsor Creek / Holy Ghost']
        elif parameters[9].value == "Sandoval":
            parameters[10].filter.list = ['126 Corridor', '485 Corridor', 'Algodones', 'Angostura', 'Areas 1,2,3 (Jemez Springs)', 'Bernalillo', 'Budaghers', 'Canada', 'Canon', 'Chaparral Girl Scout Camp', 'Cochiti Lake', 'Cochiti Mesa', 'Cochiti Pueblo', 'Corrales', 'Cuba', 'Deer Creek', 'Evergreen Hills Subdivision', 'Girl Scout Camp', 'Jemez Pueblo', 'Jemez Springs', 'La Cueva', 'La Jara', 'La Madera', 'Pena Blanca', 'Piacitas', 'Ponderosa (north)', 'Ponderosa (south)', 'Puertecito', 'Regina', 'Rio de Las Vacas', 'Rio Rancho', 'San Felipe Pueblo', 'San Ysidro', 'Santo Domingo Pueblo', 'Seven Springs', 'Sierra de los Pinos', 'Sile', 'Taylor', 'Thompson Ridge', 'Valle Grande', 'Zia Pueblo']
        elif parameters[9].value == "Santa Fe":
            parameters[10].filter.list = ['Apache Ridge', 'Arroyo Hondo', 'Bella Vista', 'Bishop\'s Lodge', 'Camel Tracks', 'Canada de los Alamos', 'Canoncito', 'Cedar Grove', 'Cerrillos', 'Chupadero', 'Cundiyo', 'Gan Eden', 'Glorieta Conference Center', 'Glorieta Estates', 'Glorieta Mesa', 'Hyde Park', 'La Barberia', 'La Ceinega', 'La Cueva Canyon', 'La Jolla', 'La Tierra', 'Lamy', 'Las Campanas', 'Los Pinos', 'Los Vaqueros', 'Lower Pacheco Canyon', 'Madrid', 'Mailbox Road', 'Ojo De La Vaca', 'Old Ranch Road', 'Old Santa Fe Trail', 'Pacheco Canyon', 'San Marcos', 'San Pedro', 'Santa Fe South', 'Sombrillo / Cuarteles', 'Sunlit Hills', 'Tano Road', 'Tesuqe', 'Thunder Mountain', 'Turquoise Trail']
        elif parameters[9].value == "Sierra":
            parameters[10].filter.list = ['Chloride', 'Cuchillo', 'Elephant Butte', 'Hillsboro', 'I-25 Corridor', 'Kingston', 'Lake Valley', 'Lake Valley Historic District', 'Lakeshore', 'Las Palomas', 'Monticello', 'Poverty Creek', 'Winston']
        elif parameters[9].value == "Socorro":
            parameters[10].filter.list = ['Abeytas', 'Bernardo', 'Bosquecito', 'Hop Canyon', 'Jarales', 'La Joya', 'Lemitar', 'Magdalena', 'Mill Canyon', 'Pueblito', 'Sabinal', 'San Acacia', 'San Antonio', 'San Pedro', 'Socorro', 'Veguita', 'Water Canyon']
        elif parameters[9].value == "Taos":
            parameters[10].filter.list = ['Amaila', 'Arroyo Hondo', 'Arroyo Seco', 'Cabresto Canyon', 'Canon', 'Carson', 'Cerro', 'Chamisal', 'Costilla', 'Desmontes, Upper / Lower', 'El Prado', 'El Salto', 'El Valle / Ojito', 'Gallina Canyon', 'Kiowa Village', 'Lama', 'Las Trampas (Trampas)', 'Latir', 'Llano Largo', 'Llano Quemado', 'Llano San Juan', 'Los Cordovas', 'Lower Des Montes', 'Lower Rio Pueblo / Golf Course', 'Ojo Caliente', 'Ojo Sarco', 'Penasco', 'Picuris Pueblo', 'Pilar', 'Pinabete Hills', 'Placita', 'Pot Creek', 'Questa', 'Ranchos De Taos', 'Red River', 'Rio Lucio', 'Rio Pueblo, lower', 'Rodarte', 'San Cristobal', 'Shady Brook', 'Sipapu', 'Stagecoach', 'Star', 'Sunshine Valley', 'Talpa', 'Taos', 'Taos Canyon / Rio Fernando', 'Taos Mesa', 'Taos Pueblo', 'Taos Ski Valley', 'Three Peaks', 'Tierra Blanca', 'Town of Red River', 'Town of Taos', 'Tres Orejas', 'Tres Piedras', 'Tres Ritos - Angostora', 'Two Peaks', 'Upper Red River Valley', 'Vadito', 'Valdez', 'Valle Escondido', 'Vallecitos', 'Ventero', \
            'Vista Linda', 'Wiemer Heights']
        elif parameters[9].value == "Torrance":
            parameters[10].filter.list = ['A102', 'Clines Corners', 'Deer Canyon Preserve', 'Duran', 'Echo Hills (Ridge)', 'Encino', 'Estancia', 'Forest Road 422', 'Forest Valley Ranch', 'Fourth of July Campground', 'Game Road', 'Homestead Estates', 'Loma Parda', 'Manzano', 'Manzano Morning', 'McIntosh', 'Mission Hills', 'Moriarty', 'Mountainair', 'Punta de Agua', 'Red Bluff', 'Sherwood Forest', 'Sunset Acres', 'Sweetwater Hills Subdivision', 'Tajique', 'Torreon', 'Willard']
        elif parameters[9].value == "Union":
            parameters[10].filter.list = ['Amistad', 'Capulin', 'Clayton', 'Des Moines', 'Folsom', 'Gladstone', 'Grenville', 'Hayden', 'Mount Dora', 'Sedan', 'Strong City', 'Thomas']
        elif parameters[9].value == "Valencia":
            parameters[10].filter.list = ['Belen', 'Bosque Farms', 'Jarales', 'Los Chavez', 'Los Lunas', 'Peralta', 'Tome', 'Valencia']
        return

    def updateMessages(self, parameters):
        # Check that Projection of Input Polygon is NAD83 UTM Zone 13N, if not set error and automatically open Help PDF for remedying this.
        if parameters[0].altered:
            polygon = parameters[0].value
            sr = arcpy.Describe(polygon).spatialReference
            if sr.name == "NAD_1983_UTM_Zone_13N":
                pass
            else:
                parameters[0].setErrorMessage(str("You need to reproject your shapefile to 'NAD83 UTM Zone 13N' prior to running this tool. Follow the steps in the PDF and feel free to contact the GIS Coordinator if you have questions."))
                referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\OARS Shapefile Developer")
                os.startfile(os.path.join(referenceFiles, "Fix Shapefile Projection.pdf"))

        if parameters[2].value in range(1000,10000):                            # Check range to be 1000-9999
            arcpy.AddMessage("Value is OK.")
        else:
            parameters[2].setErrorMessage(str("This number is out of range."))

        if parameters[4].altered:
            cid = parameters[4].valueAsText
            pattern = re.compile('[^0-9-]+')
            badChars = re.search(pattern, str(cid))
            if badChars is None:
                arcpy.AddMessage("Value is OK.")
            else:
                parameters[4].SetWarningMessage(str("Recheck the value you entered. This field only accepts numbers and a hyphen. All other character will automatically be "\
                "removed when the tool is run."))

        if parameters[11].value == True:
            referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\OARS Shapefile Developer")
            os.startfile(os.path.join(referenceFiles, "Editing Shapefile Attributes in ArcMap.pdf"))
        else: pass

        if parameters[14].altered:
            accDate = str(parameters[14].value)
            if accDate[0:10] == "1899-12-30":
                parameters[14].setErrorMessage(str("Cannot select the 'Time only' radio icon. Please select one of the other two options (OARS Shapefile Developer ignores time if 'Date and Time' selected, but correctly runs with either selected option)."))
            else:
                arcpy.AddMessage("Value is OK.")

        userCustomName = parameters[16].valueAsText
        check_for_hyphen = re.findall('[-]', str(userCustomName))               # creates a list called "check_for_hyphen"
        if len(check_for_hyphen) == 0:                                          # if list is 0 or empty
            arcpy.AddMessage("Value is OK.")
        else:
            parameters[16].SetWarningMessage(str("ESRI's geoproceesing functions contained in the 'arcpy' Python package don't allow hyphens; therefore "\
            "any hyphen(s) will automatically be removed when the tool is run. *FYI*: Hyphens ARE allowed when creating a shapefile when not using arcpy. Go figure..."))
        return

    def execute(self, parameters, messages):
        inputPolygon = parameters[0].value
        district = parameters[1].value
        workPlan = parameters[2].value
        fundNumber = parameters[3].value
        patternFinder = re.compile('[\W]+')                                     # Use a regular expression to create a match object, "re.compile" of any nonCharacters "\W", (i.e. anything that isn't a-zA-Z0-9_); "+" = match regular expression 1 or more times
        fundNumberEsri = patternFinder.sub("", fundNumber)                      # Substitute any noncharacters with a blank using the substitute method (".sub")
        cid = parameters[4].value
        patternFinder2 = re.compile('[^0-9-]+')                                 # match anything not equal to these values
        cidEsri = patternFinder2.sub("", cid)
        landowner = parameters[5].valueAsText                                   # <----- Multivalue parameter: use .valueAsText rather than .value
        landowner1 = landowner.replace(";", ", ")
        agencies = parameters[6].valueAsText                                    # <----- Multivalue parameter
        agencies1 = agencies.replace(";", ", ")
        grantTitle = parameters[7].value
        grantTitle1 = grantTitle.replace("_", " ")
        projectName = parameters[8].value
        projectName1 = projectName.replace("_", " ")
        CWPP = parameters[9].value
        CARS = parameters[10].valueAsText                                       # <---- Multivalue parameter
        CARS1 = CARS.replace(";", ", ")
        forestType = parameters[12].valueAsText                                 # <----- Multivalue parameter
        forestType1 = forestType.replace(";", ", ")
        treatment = parameters[13].valueAsText                                  # <----- Multivalue parameter
        treatment1 = treatment.replace(";", ", ")
        accDate = parameters[14].value
        fiscalYear = parameters[15].value
        userCustomName = parameters[16].value
        userCustomNameEsri = patternFinder.sub("", userCustomName)              # Use a regular expression to prevent special characters from violating ESRI naming convention.
        outputLocation = parameters[17].valueAsText

        # Reference Files
        referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\OARS Shapefile Developer")
        template = os.path.join(referenceFiles, "OARS.gdb\Data_Template_2018")

        # User specifies folder where they want shapefile saved and specifies a name
        arcpy.SetProgressor("default", "Creating a shapefile with user-specified fields...")
        arcpy.CopyFeatures_management(template, "{0}/{1}".format(outputLocation, str(userCustomNameEsri)))

        # Specify Scratch Workspace
        arcpy.env.scratchWorkspace = outputLocation
        arcpy.AddMessage("The file path & name of the input polygon is {0}".format(inputPolygon))

        # Allow logic for whether or not input polygon is a feature class / shapefile or a KML/KMZ file
        if str(inputPolygon)[-4:] in (".kmz", ".kml"): # this is equivalent to -> if str(inputPolygon)[-4:] == ".kmz" or str(inputPolygon)[-4:] == "kml":
            # Convert KML to Feature Class (KMLToLayer function also creates File Geodatabase, Feature Dataset, and a layer file i.e. "OARS_Scratch.gdb\Placemarks\Polygons"  No way to just create shapefile apparently...)
            arcpy.SetProgressorLabel("Converting KML/KMZ file to Shapefile.")
            arcpy.KMLToLayer_conversion(parameters[0].value, outputLocation, "OARS_Scratch")            # Specify name of .gdb to be "OARS_Scratch.gdb"
            tempFC1 = "{0}/OARS_Scratch.gdb/Placemarks/Polygons".format(outputLocation)                 # "Placemarks" is the default feature database name created & "Polygons" is the default name after running KML conversion function
            tempFC2 = "{0}/OARS_Scratch.gdb/tempFC2".format(outputLocation)
            sr = arcpy.SpatialReference("NAD 1983 UTM Zone 13N")                                        # Create spatial reference object
            arcpy.Project_management(tempFC1, tempFC2, sr, "WGS_1984_(ITRF00)_To_NAD_1983")             # Project the new shapefile from WGS84 to NAD83 UTM Zone 13N & use the specified geographic transformation
            arcpy.FeatureClassToShapefile_conversion(tempFC2, outputLocation)                           # convert feature class to shapefile
            inputPolygon = "{0}/tempFC2.shp".format(outputLocation)
            newfc = "{0}/{1}.shp".format(outputLocation, str(userCustomNameEsri))
            arcpy.Append_management(inputPolygon, newfc, "NO_TEST")                                     # Append shapefile from step above to template
            arcpy.Delete_management("{0}/OARS_Scratch.lyr".format(outputLocation))                      # Cleanup: delete both geodatabases, layer file, and temporary shapefile.
            arcpy.Delete_management("{0}/OARS_Scratch.gdb".format(outputLocation))
            arcpy.Delete_management("{0}/scratch.gdb".format(outpuLocation))
            arcpy.Delete_management("{0}/tempFC2.shp".format(outputLocation))
        elif str(inputPolygon)[-4:] == ".shp":
            inputPolygon = parameters[0].value
            newfc = "{0}/{1}.shp".format(outputLocation, str(userCustomNameEsri))
            arcpy.Append_management(inputPolygon, newfc, "NO_TEST")
        else:
            inputPolygon = parameters[0].value
            newfc = "{0}/{1}.shp".format(outputLocation, str(userCustomNameEsri))
            arcpy.Append_management(inputPolygon, newfc, "NO_TEST")


        #  But delete these fields if they exist
        drop_Fields = ["LAT", "LONG", "IDENT", "Name", "SHAPE_Leng", "SHAPE_Area"]  # "SHAPE_Leng" is a field from created shapefile in Append Mgmt.
        arcpy.DeleteField_management(newfc, drop_Fields)

        # Calculate fields in the appended template with user-specified values  # Can't use field names longer than some of these below, or use aliases b/c of shapefile limitations.
        arcpy.SetProgressorLabel("Now filling in 16 data fields.")
        arcpy.CalculateField_management(newfc, "Orig_Name", '"' + str(userCustomNameEsri) + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "ProjectNam", '"' + str(projectName1) + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "GrantTitle", '"' + str(grantTitle1) + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "FundNumber", '"' + str(fundNumber).upper() + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "Coop_ID", '"' + cidEsri + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "WkplanNum", workPlan, "PYTHON")
        arcpy.CalculateField_management(newfc, "District", '"' + district + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "Landowner", '"' + str(landowner1).replace("'", "") + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "AgencyInv", '"' + str(agencies1).replace("'", "") + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "CWPP", '"' + CWPP + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "CARS", '"' + str(CARS1).replace("'", "") + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "ForestType", '"' + str(forestType1).replace("'", "") + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "Treatment", '"' + str(treatment1).replace("'", "") + '"', "PYTHON")

        # Convert both accomplishment & input dates to format that ArcGIS requires (Reference: ArcGIS field data types)
        accDateEsri = accDate.strftime("%m/%d/%Y %H:%M:%S %p")                  # Time won't appear in shapefile b/c that's a limitation of shapefiles - only accept dates, not time.
        arcpy.CalculateField_management(newfc, "AccompDate", '"' + accDateEsri + '"', "PYTHON")
        now = datetime.now()
        inputDateEsri = now.strftime("%m/%d/%Y %H:%M:%S %p")
        arcpy.CalculateField_management(newfc, "Input_Date", '"' + inputDateEsri + '"', "PYTHON")
        arcpy.CalculateField_management(newfc, "FY", fiscalYear, "PYTHON")
        arcpy.CalculateField_management(newfc, "Acres", "!shape.area@acres!", "PYTHON")

        # Add Formatted Shapefile to MXD if user wants.
        if parameters[18].value == True:
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            arcpy.MakeFeatureLayer_management(newfc, "{0}_map".format(userCustomNameEsri))
            OARS = arcpy.mapping.Layer("{0}_map".format(userCustomNameEsri))
            OARS.name = "{0}".format(userCustomName)
            arcpy.mapping.AddLayer(df, OARS, "TOP")
            arcpy.Delete_management("{0}_map".format(userCustomNameEsri))
        else: pass

        # If user chooses to also create a KMZ file (compressed KML), create it so that the attributes are exactly like the shapefile:
        if parameters[19].value == True:
            arcpy.SetProgressorLabel("Now creating a KMZ file called {0}".format(str(userCustomNameEsri)))
            arcpy.MakeFeatureLayer_management("{0}/{1}.shp".format(outputLocation, str(userCustomNameEsri)), "{0}_kml".format(userCustomNameEsri)) # str(userCustomNameEsri))
            arcpy.LayerToKML_conversion("{0}_kml".format(userCustomNameEsri), "{0}/{1}.kmz".format(outputLocation, str(userCustomNameEsri)), "", "NO_COMPOSITE", "", "", "", "CLAMPED_TO_GROUND")
            arcpy.Delete_management("{0}_kml".format(userCustomNameEsri))
        else: pass
        return

class PercentSlopeAnalysis(object):
    def __init__(self):
        self.label = "Percent Slope Analysis"
        self.description = "This tool takes a user-provided shapefile and calculates percent slope (i.e., percent rise as opposed to slope inclination calculated in degrees). It calculates acreage of land occurring\
        on steep and less steep slopes using the slope threshold chosen by the user (15%, 20%, 25%, 30% or 40%). Outputs from this tool include a graph (PDF) summarizing acreage by polygon, as well as a map (PDF) that labels the polygons for your \
        reference and uses symbolgy to depict areas of steep and less steep slopes. A shapefile depicting the boundaries of steep and less steep slopes is also created that includes the attributes used to create the graph and map in case you want \
        to create your own graphs or maps. This tool could be useful to TMOs on forest management projects by providing slope information on potential treatments or timber harvests to correctly setup contractor rates, which may vary by slope."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Input Polygon",
            name = "Input Polygon",
            datatype = ["DEFeatureClass", "DEShapefile", "GPFeatureLayer"],
            parameterType = "Required",
            direction = "Input")
        param1 = arcpy.Parameter(
            displayName = "Choose Output Folder on your Local Drive",
            name = "Output Folder",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input")
        param2 = arcpy.Parameter(
            displayName = "Name for Output Files",
            name = "Name for Output Files",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")
        param3 = arcpy.Parameter(
            displayName = "Slope Threshold",
            name = "Slope Threshold",
            datatype = "GPLong",
            parameterType = "Required",
            direction = "Input")
        param3.filter.type = "ValueList"
        param3.filter.list = [15, 20, 25, 30, 40]
        param3.value = 20       # set default value
        param4 = arcpy.Parameter(
            displayName = "Save MXD file(s)?",
            name = "Save MXD file(s)?",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        # Check that Projection of Input Polygon is NAD83 UTM Zone 13N
        if parameters[0].altered:
            polygon = parameters[0].value
            sr = arcpy.Describe(polygon).spatialReference
            if sr.name == "NAD_1983_UTM_Zone_13N":
                pass
            else:
                parameters[0].setErrorMessage(str("You need to reproject your polygon to the correct projection, NAD83 UTM Zone 13N, prior to running this tool."))
                referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\Polygon Slope Analysis")
                os.startfile(os.path.join(referenceFiles, "Fix Shapefile Projection_slope.pdf"))
        return

    def execute(self, parameters, messages):
        # User-provided input
        polygon = parameters[0].value
        output_folder = parameters[1].valueAsText
        patternFinder = re.compile('[\W]+')
        name = parameters[2].value
        nameEsri = patternFinder.sub("", name)                                  # Regular Expression to make sure no illegal characters used for file names (those characters will be allowed for map title however)
        slope_threshold = parameters[3].value

        # Script Reference Files
        env.overwriteOutput = True
        referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\Polygon Slope Analysis")
        slope_15 = arcpy.Raster(os.path.join(referenceFiles, "slope_15%.tif"))
        slope_20 = arcpy.Raster(os.path.join(referenceFiles, "slope_20%.tif"))
        slope_25 = arcpy.Raster(os.path.join(referenceFiles, "slope_25%.tif"))
        slope_30 = arcpy.Raster(os.path.join(referenceFiles, "slope_30%.tif"))
        slope_40 = arcpy.Raster(os.path.join(referenceFiles, "slope_40%.tif"))
        slope_15_lyr = os.path.join(referenceFiles, "Slope_15%.lyr")
        slope_20_lyr = os.path.join(referenceFiles, "Slope_20%.lyr")
        slope_25_lyr = os.path.join(referenceFiles, "Slope_25%.lyr")
        slope_30_lyr = os.path.join(referenceFiles, "Slope_30%.lyr")
        slope_40_lyr = os.path.join(referenceFiles, "Slope_40%.lyr")
        graph_Template = os.path.join(referenceFiles, "Slope Summary_Simple.grf") # Referenced in part 2 of Script
        mxd_template = arcpy.mapping.MapDocument(os.path.join(referenceFiles, "slope_basemap.mxd"))  # Referenced in part 3 of script
        Output_mxd = "{0}/{1}_Map_{2}_{3}_{4}.mxd".format(output_folder, nameEsri, now.month, now.day, now.year)  # temp map document needed b/c saving map would alter map template

        # Add unique field in order to label zones
        arcpy.SetProgressor("default", "Peforming percent slope analysis...")
        arcpy.AddField_management(polygon, "Zone", "TEXT", "", "", 15)

        # Work-around to Error 000728 --- subsequent code points to new shapefile
        # Create layer & save to refresh (avoids reoccuring error when try to just work on FC)
        arcpy.MakeFeatureLayer_management(polygon, 'polygonLayer')
        arcpy.CopyFeatures_management('polygonLayer', "{0}/{1}_Zone_Labels.shp".format(output_folder, nameEsri))
        refresh_poly = "{0}/{1}_Zone_Labels.shp".format(output_folder, nameEsri)

        # Expression to populate new "Zone" field
        expression = "autoIncrement(!FID!)"
        codeblock = """def autoIncrement(fid):
            fid = int(fid)
            fid += 1
            return "Polygon " + str(fid)"""
        arcpy.CalculateField_management(refresh_poly, "Zone", expression, "PYTHON", codeblock)

        # Save copy of reclassified slope raster overlapping input polygon's extent
        arcpy.SetProgressorLabel("Clipping reclassified slope raster that overlaps polygon's extent...")
        if slope_threshold == 15:
            arcpy.Clip_management(slope_15, "", "{0}/{1}_slope.tif".format(output_folder, nameEsri), polygon, "", "ClippingGeometry", "NO_MAINTAIN_EXTENT")   # Clip slope raster using input polygon. Make raster spatial extent same as input polygon, but allow slight adjusments to extent based on slope raster grid cells
        elif slope_threshold == 20:
            arcpy.Clip_management(slope_20, "", "{0}/{1}_slope.tif".format(output_folder, nameEsri), polygon, "", "ClippingGeometry", "NO_MAINTAIN_EXTENT")
        elif slope_threshold == 25:
            arcpy.Clip_management(slope_25, "", "{0}/{1}_slope.tif".format(output_folder, nameEsri), polygon, "", "ClippingGeometry", "NO_MAINTAIN_EXTENT")
        elif slope_threshold == 30:
            arcpy.Clip_management(slope_30, "", "{0}/{1}_slope.tif".format(output_folder, nameEsri), polygon, "", "ClippingGeometry", "NO_MAINTAIN_EXTENT")
        elif slope_threshold == 40:
            arcpy.Clip_management(slope_40, "", "{0}/{1}_slope.tif".format(output_folder, nameEsri), polygon, "", "ClippingGeometry", "NO_MAINTAIN_EXTENT")

        # Convert raster to vector
        arcpy.SetProgressorLabel("Convert raster to polygon...")
        slope = arcpy.Raster("{0}/{1}_slope.tif".format(output_folder, nameEsri))
        arcpy.RasterToPolygon_conversion(slope, "{0}/{1}_binarySlope.shp".format(output_folder, nameEsri), "SIMPLIFY", "VALUE")

        # Intersect analysis in order to populate zone number to every record of binarySlope
        arcpy.SetProgressorLabel("Label each record with polygon number...")
        binarySlope = "{0}/{1}_binarySlope.shp".format(output_folder, nameEsri)
        arcpy.Intersect_analysis([refresh_poly, binarySlope], "{0}/{1}_intersect.shp".format(output_folder, nameEsri) , "ALL")
        intersect = "{0}/{1}_intersect.shp".format(output_folder, nameEsri)

        # Add Acres field, calculate geometry and Add slope field and populate it (use slope field instead of GRIDCODE for interpretability)
        arcpy.SetProgressorLabel("Add 'Acres' field and calculate...")
        arcpy.AddField_management(intersect, "Acres", "DOUBLE")
        arcpy.CalculateField_management(intersect, "Acres", "!shape.area@acres!", "PYTHON")
        arcpy.AddField_management(intersect, "Slope", "TEXT", "", "", 20)
        expression = "slopeVal(!GRIDCODE!)"
        if slope_threshold == 15:
            codeblock = """def slopeVal(grid):
                degree_sign = u'\N{DEGREE SIGN}'
                if grid == 0:
                    return "> 15%"
                elif grid == 1:
                    return "< 15%" """
        elif slope_threshold == 20:
            codeblock = """def slopeVal(grid):
                degree_sign = u'\N{DEGREE SIGN}'
                if grid == 0:
                    return "> 20%"
                elif grid == 1:
                    return "< 20%" """
        elif slope_threshold == 25:
            codeblock = """def slopeVal(grid):
                degree_sign = u'\N{DEGREE SIGN}'
                if grid == 0:
                    return "> 25%"
                elif grid == 1:
                    return "< 25%" """
        elif slope_threshold == 30:
            codeblock = """def slopeVal(grid):
                degree_sign = u'\N{DEGREE SIGN}'
                if grid == 0:
                    return "> 30%"
                elif grid == 1:
                    return "< 30%" """
        elif slope_threshold == 40:
            codeblock = """def slopeVal(grid):
                degree_sign = u'\N{DEGREE SIGN}'
                if grid == 0:
                    return "> 40%"
                elif grid == 1:
                    return "< 40%" """
        arcpy.CalculateField_management(intersect, "Slope", expression, "PYTHON", codeblock)

        # Dissolve & sum acres by zone and gridcode (1 = below slope threshold, 0 above slope threshold)
        arcpy.Dissolve_management(intersect, "{0}/{1}_Slope{2}_Summary.shp".format(output_folder, nameEsri, slope_threshold), dissolve_field="Zone;Slope", statistics_fields="Acres SUM", multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")
        final = "{0}/{1}_Slope{2}_Summary.shp".format(output_folder, nameEsri, slope_threshold)

        # Sum Acres of ALL polygons above and below slope threshold  (Info to be used in Map Subtitle in Part 4)
        query = """ "Slope" = '> 15%' OR "Slope" = '> 20%' OR "Slope" = '> 25%' OR "Slope" = '> 30%' OR "Slope" = '> 40%' """    # Very steep
        SteepCursor = arcpy.da.SearchCursor(final, ["Slope", "SUM_Acres"], query)
        SteepSum = 0
        for row in SteepCursor:
            SteepSum += row[1]
        query2 = """ "Slope" = '< 15%' OR "Slope" = '< 20%' OR "Slope" = '< 25%' OR "Slope" = '< 30%' OR "Slope" = '< 40%' """   # Less steep
        FlatCursor = arcpy.da.SearchCursor(final, ["Slope", "SUM_Acres"], query2)
        FlatSum = 0
        for row in FlatCursor:
            FlatSum += row[1]

        # Add "Graph Label" field that combines zone & slope for graph creation
        arcpy.AddField_management(final, "GraphLabel", "TEXT", "", "", 30)
        expression = "graphLabel(!Zone!, !Slope!)"
        codeblock = """def graphLabel(zone, slope):
            return zone + ": " + slope"""
        arcpy.CalculateField_management(final, "GraphLabel", expression, "PYTHON", codeblock)

        ########################################################################
        # Part 2 - Create Graphs Summarizing Slope
        ########################################################################
        arcpy.MakeGraph_management(graph_Template, "SERIES=bar:vertical DATA={0} Y=SUM_Acres LABEL=GraphLabel;GRAPH=general TITLE={1} Percent Slope Results FOOTER=New Mexico State Forestry;LEGEND=general;AXIS=left TITLE=Acres;AXIS=right;AXIS=bottom;AXIS=top".format(final, name), "temp_graph")
        arcpy.SaveGraph_management("temp_graph", "{0}/{1}_{2}%_Slope_Graph.pdf".format(output_folder, nameEsri, slope_threshold), "MAINTAIN_ASPECT_RATIO", "1000", "559")

        ########################################################################
        # Part 3 - Create Slope Analsyis Summary Map with Labeled Polygons
        ########################################################################
        # Define Dataframes
        arcpy.SetProgressorLabel("Creating PDF map displaying slope analysis...")
        df_main = arcpy.mapping.ListDataFrames(mxd_template, "Main Map")[0]
        df_inset = arcpy.mapping.ListDataFrames(mxd_template, "Inset Map")[0]

        # Make treatment boundaries a layer and add to map
        arcpy.MakeFeatureLayer_management(final, "{0}".format(nameEsri))
        treatments = arcpy.mapping.Layer("{0}".format(nameEsri))                            # feature layer object
        arcpy.mapping.AddLayer(df_main, treatments, "TOP")

        # Add symbology to Treatments (based on slope threshold) & add transparency
        updateLayer = arcpy.mapping.ListLayers(mxd_template, treatments, df_main)[0]    # the map layer object
        if slope_threshold == 15:
            sourceLayer = arcpy.mapping.Layer(slope_15_lyr)
        elif slope_threshold == 20:
            sourceLayer = arcpy.mapping.Layer(slope_20_lyr)
        elif slope_threshold == 25:
            sourceLayer = arcpy.mapping.Layer(slope_25_lyr)
        elif slope_threshold == 30:
            sourceLayer = arcpy.mapping.Layer(slope_30_lyr)
        elif slope_threshold == 40:
            sourceLayer = arcpy.mapping.Layer(slope_40_lyr)
        arcpy.mapping.UpdateLayer(df_main, updateLayer, sourceLayer)
        updateLayer.transparency = 50  # has to be the map layer object, can't be the feature layer object (i.e. treatments)

        # Simplify shapefile for labeling (1 label per polygon)
        arcpy.Dissolve_management(final, "{0}/{1}_simplified.shp".format(output_folder, nameEsri), "Zone")
        arcpy.MakeFeatureLayer_management("{0}/{1}_simplified.shp".format(output_folder, nameEsri), "{0}_labels".format(nameEsri))
        labels_lyr = arcpy.mapping.Layer("{0}_labels".format(nameEsri))

        legend = arcpy.mapping.ListLayoutElements(mxd_template, "LEGEND_ELEMENT", "Legend")[0]
        legend.autoAdd = False      # Prevents layer used for labeling from showing up in legend.
        arcpy.mapping.AddLayer(df_main, labels_lyr, "BOTTOM")

        # Label Treatments
        labels_lyr = arcpy.mapping.ListLayers(mxd_template, "{0}_labels".format(nameEsri))[0]  # Explictily specify layer in order for next 2 commands to work
        labels_lyr.labelClasses[0].expression = "[Zone]"   # Specify field to label
        labels_lyr.showLabels = True

        # Zoom Main Map extent to Treatments
        Extent = treatments.getExtent(True)
        df_main.extent = Extent
        df_main.scale = df_main.scale * 1.05   # Zoom out just a tad.

        # Zoom Inset Map Extent to Correct Counties
        arcpy.mapping.AddLayer(df_inset, treatments, "TOP")                             # Add treatments to inset map data frame
        treatmentsInset = arcpy.mapping.ListLayers(mxd_template, treatments, df_inset)[0]  # Create treatments inset map layer object
        arcpy.mapping.UpdateLayer(df_inset, treatmentsInset, sourceLayer)
        countiesInset = arcpy.mapping.ListLayers(mxd_template, "County Boundaries", df_inset)[0] # Create county boundaries inset map layer object
        arcpy.SelectLayerByLocation_management(countiesInset, "INTERSECT", treatmentsInset)   # Intersect counties with treatments
        df_inset.extent = countiesInset.getSelectedExtent()
        arcpy.SelectLayerByAttribute_management(countiesInset, "CLEAR_SELECTION")
        df_inset.scale = df_inset.scale * 1.05

        # Update map elements
        newTitle = name.title()             # allow characters illegal for file names

        # Format Subtitle - subtitle will summarize acreage above and below slope threshold
        steepList = list(str(format(SteepSum, '.2f')))
        if len(steepList) == 7:
            steepList.insert(1, ',')
            steepFormatted = ''.join(steepList)
        elif len(steepList) == 8:
            steepList.insert(2, ',')
            steepFormatted = ''.join(steepList)
        elif len(steepList) == 9:
            steepList.insert(3, ',')
            steepFormatted = ''.join(steepList)
        elif len(steepList) == 10:
            steepList.insert(1, ',')
            steepList.insert(4, ',')
            steepFormatted = ''.join(steepList)
        elif len(steepList) == 11:
            steepList.insert(2, ',')
            steepList.insert(5, ',')
            steepFormatted = ''.join(steepList)
        elif len(steepList) == 12:
            steepList.insert(3, ',')
            steepList.insert(6, ',')
            steepFormatted = ''.join(steepList)
        else:
            steepFormatted = ''.join(steepList)
        flatList = list(str(format(FlatSum, '.2f')))
        if len(flatList) == 7:
            flatList.insert(1, ',')
            flatFormatted = ''.join(flatList)
        elif len(flatList) == 8:
            flatList.insert(2, ',')
            flatFormatted = ''.join(flatList)
        elif len(flatList) == 9:
            flatList.insert(3, ',')
            flatFormatted = ''.join(flatList)
        elif len(flatList) == 10:
            flatList.insert(1, ',')
            flatList.insert(4, ',')
            flatFormatted = ''.join(flatList)
        elif len(flatList) == 11:
            flatList.insert(2, ',')
            flatList.insert(5, ',')
            flatFormatted = ''.join(flatList)
        elif len(flatList) == 12:
            flatList.insert(3, ',')
            flatList.insert(6, ',')
            flatFormatted = ''.join(flatList)
        else:
            flatFormatted = ''.join(flatList)
        newSubtitle = ">{0}% Slope: {1} Acres;   <{2}% Slope: {3} Acres".format(slope_threshold, steepFormatted, slope_threshold, flatFormatted)
        date = now.strftime("%B %d, %Y")
        newMapNotes = "{0} {1}\n{2}".format("NMSF", date, "NAD83 UTM Zone 13N")
        myElements = arcpy.mapping.ListLayoutElements(mxd_template, "TEXT_ELEMENT")
        for element in myElements:
            if element.name == "Map Title":
                element.text = newTitle
            elif element.name == "Map Subtitle":
                element.text = newSubtitle
            elif element.name == "Map Notes":
                element.text = newMapNotes

        # Specify Scale Bar as meters or miles dependent on data frame scale.
        met_scale = arcpy.mapping.ListLayoutElements(mxd_template, "MAPSURROUND_ELEMENT", "Scale Bar - meters")[0]
        mil_scale = arcpy.mapping.ListLayoutElements(mxd_template, "MAPSURROUND_ELEMENT", "Scale Bar - miles")[0]
        if df_main.scale < 25000:
            met_scale.elementPositionX = 1.936    # On the page
            mil_scale.elementPositionX = 15       # Move scale bar off the page
        else:
            met_scale.elementPositionX = 15
            mil_scale.elementPositionX = 1.936

        # Specify Scale Bar text below scale bar (e.g., 1:100,000    1 inch = 1.58 miles)
        scaleText = arcpy.mapping.ListLayoutElements(mxd_template, "TEXT_ELEMENT", "Scale Text")[0]

        # 1a) Format Scale by putting in commas for thousand dividers.
        scaleList = list(str(int(df_main.scale)))
        if len(scaleList) > 3 and len(scaleList) <= 6:
            scaleList.insert(3, ',')
            scaleFormatted = ''.join(scaleList)
        elif len(scaleList) >=7 and len(scaleList) <= 9:
            scaleList.insert(3, ',')
            scaleList.insert(7, ',')
            scaleFormatted = ''.join(scaleList)
        elif len(scaleList) >= 10 and len(scaleList) <=12:
            scaleList.insert(3, ',')
            scaleList.insert(7, ',')
            scaleList.insert(11,',')
            scaleFormatted = ''.join(scaleList)
        else:
            pass

        # 1b) Specify whether to use meters or miles scale bar based on map scale.
        if df_main.scale < 25000:
            meters = df_main.scale/100
            scaleText.text = "1: {0}  1 inch = {1} meters".format(scaleFormatted, str(round(meters,2)))
        else:
            feet = df_main.scale/12   # Convert inches to feet
            miles = feet/5280          # Convert feet to miles
            scaleText.text = "1:{0}  1 inch = {1} miles".format(scaleFormatted, str(round(miles,2)))

        # Save then export mapdocument to PDF
        arcpy.ResetProgressor()
        arcpy.SetProgressorLabel("Now saving {0}_{1}%_Slope_Map.pdf at your chosen folder: {2}. Also deleting tempoary files created by the script. This final step takes awhile...".format(nameEsri, slope_threshold, output_folder))
        mxd_template.saveACopy(Output_mxd)
        arcpy.mapping.ExportToPDF(mxd_template, "{0}/{1}_{2}%_Slope_Map.pdf".format(output_folder, nameEsri, slope_threshold))

        # Does user choose to save mxd file?
        if parameters[4].altered:
            pass
        else:
            arcpy.Delete_management(Output_mxd)

        ########################################################################
        # Part 4 - Script Cleanup
        ########################################################################
        del mxd_template
        arcpy.Delete_management("in_memory")
        arcpy.DeleteField_management(polygon, "Zone")                           # Even when adding this field to layer, "Zone" gets added to original shapefile...
        arcpy.Delete_management("{0}/{1}_Zone_Labels.shp".format(output_folder, nameEsri))
        arcpy.Delete_management("{0}/{1}_binarySlope.shp".format(output_folder, nameEsri))
        arcpy.Delete_management("{0}/{1}_intersect.shp".format(output_folder, nameEsri))
        arcpy.Delete_management("{0}/{1}_slope.tif".format(output_folder, nameEsri))
        arcpy.Delete_management("{0}/{1}_simplified.shp".format(output_folder, nameEsri))  # the shapefile that was created simply for map labeling purposes

        # Lastly, automatically open the map & graph
        os.startfile("{0}/{1}_{2}%_Slope_Map.pdf".format(output_folder, nameEsri, slope_threshold))
        os.startfile("{0}/{1}_{2}%_Slope_Graph.pdf".format(output_folder, nameEsri, slope_threshold))
        return

class ShapefileToWKT(object):
    def __init__(self):
        self.label = "Convert Shapefile to WKT"
        self.description = "This tool converts a shapefile to Well-known text (WKT) and writes the WKT to a text file (.txt)."\
        "WKT specifies the type of geometric object (e.g. MULTIPOLYGON, MULTIPOINT) and then specifies each vertex by an XY pair separated by commas contained within a set of parentheses. Prior to conversion to WKT, "\
        "the tool reprojects the shapefile(s) to the Web Mercator Projection, which is the projection that the SMART web-based data entry tool expects. This tool can be used in place of either the USFS ShapeUp Addin or"\
        "the SMART Shape Up program that starts by running an executable file (Esri independent tool). All 3 tools accomplish the same task."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Input Shapefile",
            name = "Input Shapefile",
            datatype = ["DEFeatureClass", "DEShapefile", "GPFeatureLayer"],     # Set both Feature class and shapefile as allowable inputs
            parameterType = "Required",
            direction = "Input")
        param1 = arcpy.Parameter(
            displayName = "Choose Output Folder on Local Drive",
            name = "Choose Output Folder on Local Drive",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input")
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        param1.value = desktop
        param1.filter.list = ["File System"]                                    # Set filter to only accept a folder
        param2 = arcpy.Parameter(
            displayName = "Open Help Document for this tool?",
            name = "WKT_Help_Document",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input")

        params = [param0, param1, param2]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        if parameters[0].altered:
            polygon = parameters[0].value
            crs = arcpy.Describe(polygon).spatialReference
            if crs.name in ("WGS_1984_Web_Mercator_Auxiliary_Sphere", "GCS_WGS_1984", "NAD_1983_UTM_Zone_12N", "NAD_1983_UTM_Zone_13N"):
                pass
            else:
                parameters[0].setErrorMessage("You need to reproject your polygon to the correct projection, NAD83 UTM Zone 13N, prior to running this tool.")
                referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\Convert Shapefile to WKT")
                os.startfile(os.path.join(referenceFiles, "Fix Shapefile Projection_WKT.pdf"))

        if parameters[2].value == True:
            referenceFiles = os.path.join(os.path.dirname(__file__), "Reference Files - Please don't alter\Convert Shapefile to WKT")
            os.startfile(os.path.join(referenceFiles, "Convert Shapefile to WKT Help Document.pdf"))
        else: pass
        return

    def execute(self, parameters, messages):
        inputPolygon = parameters[0].value
        outputLocation = parameters[1].valueAsText
        crs = arcpy.Describe(inputPolygon).spatialReference
        polygonName = parameters[0].valueAsText
        pattern = re.compile('[\W]+')                                           # Regex to create match object, "re.compile" of any nonCharacters "\W", (i.e. anything that isn't a-zA-Z0-9_); "+" = match regular expression 1 or more times
        polygonName = pattern.sub("", polygonName)

        # Setup environment variables and create temp files before branching logic so to only create them once.
        env.overwriteOutput = True
        env.outputZFlag = "Disabled"                                            # necessary b/c some shapefiles have 'Polygon' as shape while others have 'Polygon Z'
        env.outputMFlag = "Disabled"                                            # necessary b/c some shapefiles have 'Polygon' as shape while others have 'Polygon M'
        tempFC1 = "{0}/temp.shp".format(outputLocation)
        textFile = "{0}/{1}_WKT.txt".format(outputLocation, polygonName)        # Create empty textfile with name of input shapefile and "_WKT" appended.

        if crs.name == "WGS_1984_Web_Mercator_Auxiliary_Sphere":                # If input CRS matches Web Mercator there's no need to reproject to Web Mercator
            outFile = open(textFile, "w")
            with arcpy.da.SearchCursor(inputPolygon, ["SHAPE@WKT"]) as cursor:  # Use cursor to go row by row to print WKT information.
                for row in cursor:
                    outFile.write((row[0]))
            outFile.close()
            f = open(textFile, "r+")                                            # Code from this line to next 7 lines removes any instances of ")MULTIPOLYGON (" and replaces it with ", " so the text can be successfully copied and pasted into USFS website.
            lines = f.readlines()
            for line in lines:
                pattern = re.compile(r'\)MULTIPOLYGON\s\(')                     # this matches ")MULTIPOLYGON (" exactly.
                text_edited = pattern.sub(", ", line)                           # substitute the pattern with ", "
                f.seek(0)                                                       # go to start of file
                f.writelines(text_edited)                                       # now write and implement the changes to the original text file.
            f.close()                                                           # closes the text file
        elif crs.name == "GCS_WGS_1984":                                        # If input CRS matches WGS 1984, reproject to Web Mercator
            arcpy.Project_management(inputPolygon, tempFC1, 3857)               # 3857 = WKID (Well-known ID) of WGS_1984_Web_Mercator_Auxiliary_Sphere
            outFile = open(textFile, "w")
            with arcpy.da.SearchCursor(tempFC1, ["SHAPE@WKT"]) as cursor:
                for row in cursor:
                    outFile.write((row[0]))
            outFile.close()
            f = open(textFile, "r+")
            lines = f.readlines()
            for line in lines:
                pattern = re.compile(r'\)MULTIPOLYGON\s\(')
                text_edited = pattern.sub(", ", line)
                f.seek(0)
                f.writelines(text_edited)
            f.close()
        elif crs.name in ("NAD_1983_UTM_Zone_12N", "NAD_1983_UTM_Zone_13N"):    # If input CRS matches NAD 1983 UTM Z13N or 12N, reproject to Web Mercator
            arcpy.Project_management(inputPolygon, tempFC1, 3857, "WGS_1984_(ITRF00)_To_NAD_1983")
            outFile = open(textFile, "w")
            with arcpy.da.SearchCursor(tempFC1, ["SHAPE@WKT"]) as cursor:
                for row in cursor:
                    outFile.write((row[0]))
            outFile.close()
            f = open(textFile, "r+")
            lines = f.readlines()
            for line in lines:
                pattern = re.compile(r'\)MULTIPOLYGON\s\(')
                text_edited = pattern.sub(", ", line)
                f.seek(0)
                f.writelines(text_edited)
            f.close()
            f = open(textFile, "r+")
            lines = f.readlines()
        arcpy.Delete_management(tempFC1)
        return