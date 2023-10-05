# Description


# TODO
# Add a check if the gpx-file in new folder already exists in processed folder. So files are not processed multiple times

# Requirements
import os
import geopandas as gpd
import pandas as pd
import pathlib

# Variables
new_gpx_foldername = 'new_gpxfiles'
new_gpx_directory = pathlib.Path('.').absolute() / new_gpx_foldername 

processed_gpx_foldername = 'processed_gpxfiles'
processed_gpx_directory = pathlib.Path('.').absolute() / processed_gpx_foldername 

hexagonfilename = 'hexagonNetherlands.json'
hexagonfile = pathlib.Path('.').absolute() / hexagonfilename

# Temporary gpd to store information per run
temp_gdf_hexagons_per_run = []

# Proces per gpx-file
for filename in os.listdir(new_gpx_directory):
    if filename.endswith('.gpx'):
        gpxfile = os.path.join(new_gpx_directory, filename)
        
        gpx = gpd.read_file(gpxfile, layer='tracks')

        gdf_gpxline = gpx[gpx['name'].str.contains("Running")]
        
        date = filename[:10]
        gdf_gpxline['date'] = date
        
        # Replace 'path/to/your/file.geojson' with the actual file path
        #file_path = 'C:/Projects/RunningHexagons/data/hexagonNetherlands.geojson'
        polygon = gpd.read_file(hexagonfile)

        # Perform the intersection
        gdf_join = gpd.sjoin(left_df=polygon, right_df=gdf_gpxline,  how="inner", predicate="intersects")
        #print(gdf_join)
        
        #Append data to temp gdf
        temp_gdf_hexagons_per_run.append(gdf_join)

# Create gdf with information from all gpx-files
gdf_new = gpd.GeoDataFrame( pd.concat(temp_gdf_hexagons_per_run, ignore_index=True) )

# Calculate information per hexagons (number of runs, first date and last date)
df_new_count = gdf_new.groupby('uuid', as_index=False).agg(count=('uuid', 'count'))
df_new_first_date = gdf_new.groupby('uuid', as_index=False).agg(first_date=('date', 'min'))
df_new_last_date = gdf_new.groupby('uuid', as_index=False).agg(last_date=('date', 'max'))

# Merge information per hexagon in one df
df_new_all = pd.merge(df_new_count, df_new_first_date, on=["uuid"])
df_new_all = pd.merge(df_new_all, df_new_last_date, on=["uuid"])

# Merge geometry (gdf) with attribute information (df)
gdf_new_temp = gdf_new.merge(df_new_all, on=["uuid"])

gdf_new_complete = gdf_new_temp.drop_duplicates(subset=['uuid'])

# Select columsn
col_list = ['uuid', 'count', 'first_date', 'last_date', 'geometry']
gdf_new_complete = gdf_new_complete[col_list]
#gdf_new_complete.to_file("gdf_new_complete.geojson", driver='GeoJSON')

###########
### Merge dataframe of new gpx files with existing hexagons.geojson
# Proces is split into two parts, geometry and attributes, which are merged later

# Import existing Running Hexagons file
rh_filename = 'runninghexagons.geojson'
rh_file = pathlib.Path('.').absolute() / rh_filename
gdf_existing = gpd.read_file(rh_file)


### GEOMETRY
col_list_merge = ['uuid', 'geometry']

gdf_existing_geometry_merge = gdf_existing[col_list_merge]
gdf_new_geometry_merge = gdf_new_complete[col_list_merge]

gdf_geometry_merged = pd.concat([gdf_existing_geometry_merge, gdf_new_geometry_merge])

# Drop duplicates
gdf_geometry_merged = gdf_geometry_merged.drop_duplicates(subset=['uuid'])
#gdf_geometry_merged.to_file("gdf_geometry_merged.geojson", driver='GeoJSON')

### END GEOMETRY

### ATTRIBUTES

## Calculate attributes count, first_date and last_date from new gpx-files

# Existing
df_existing_attr = pd.DataFrame(gdf_existing)
col_list_attr = ['uuid', 'count', 'first_date', 'last_date']
df_existing_attr = df_existing_attr[col_list_attr]
#df_existing_attr.to_csv("df_existing_attr.csv", sep=';', header=True)

# New
df_new_attr = pd.DataFrame(gdf_new_complete)
df_new_attr = df_new_attr[col_list_attr]
#df_new_attr.to_csv("df_new_attr.csv", sep=';', header=True)

#Concatanete existing en new information
df_attr_concat = pd.concat([df_existing_attr, df_new_attr])
#df_attr_concat.to_csv("df_attr_concat.csv", sep=';', header=True)

#### DIT MOET NOG GEFIXT WORDEN

# SUM - count
df_all_count = df_attr_concat.groupby(['uuid'])['count'].agg('sum')

# MIN - first_date
df_all_first_date = df_attr_concat.groupby('uuid', as_index=False).agg(first_date=('first_date', 'min'))

# MAX - last_date
df_all_last_date = df_attr_concat.groupby('uuid', as_index=False).agg(last_date=('last_date', 'max'))

# Merge information
df_all_attr_merged = pd.merge(df_all_count, df_all_first_date, how = 'inner', on=["uuid"])
df_all_attr_merged = pd.merge(df_all_attr_merged, df_all_last_date, on=["uuid"])
#df_all_attr_merged.to_csv("df_rh_all_attr_merged.csv", sep=';', header=True)

### END ATTRIBUTES

### MERGE GEOMETRY AND ATTRIBUTES
# Merge geometry (gdf) with attribute information (df)
gdf_all_runs = gdf_geometry_merged.merge(df_all_attr_merged, on=["uuid"])


# Move data from new_gpxfiles dir to processed_gpxfiles dir
# Move files before writing the geojson, if there are files already in the processed folder the script stops, so no files are not processed multiple times
# Gather all files in source folder
allfiles = os.listdir(new_gpx_directory)
 
# Iterate on all files to move them to destination folder
for f in allfiles:
    src_path = os.path.join(new_gpx_directory, f)
    dst_path = os.path.join(processed_gpx_directory, f)
    os.rename(src_path, dst_path)

### Write geojsonfile
if(os.path.isfile("runninghexagons.geojson")):
    os.remove("runninghexagons.geojson")
    print("File Deleted successfully")
else:
    print("File does not exist")


gdf_all_runs.to_file("runninghexagons.geojson", driver='GeoJSON')

