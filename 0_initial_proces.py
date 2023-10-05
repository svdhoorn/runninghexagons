# Description

# Requirements
import os
import geopandas as gpd
import pandas as pd
import pathlib
#import matplotlib.pyplot as plt

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
gdf_rh = gpd.GeoDataFrame( pd.concat(temp_gdf_hexagons_per_run, ignore_index=True) )

# Calculate information per hexagons (number of runs, first date and last date)
df_count = gdf_rh.groupby('uuid', as_index=False).agg(count=('uuid', 'count'))
df_first_date = gdf_rh.groupby('uuid', as_index=False).agg(first_date=('date', 'min'))
df_last_date = gdf_rh.groupby('uuid', as_index=False).agg(last_date=('date', 'max'))

# Merge information per hexagon in one df
df_all_attr = pd.merge(df_count, df_first_date, on=["uuid"])
df_all_attr = pd.merge(df_all_attr, df_last_date, on=["uuid"])

# Merge geometry (gdf) with attribute information (df)
gdf_temp = gdf_rh.merge(df_all_attr, on=["uuid"])

gdf_complete = gdf_temp.drop_duplicates(subset=['uuid'])

# Select columsn
col_list = ['uuid', 'count', 'first_date', 'last_date', 'geometry']
gdf_complete = gdf_complete[col_list]

# Write geojsonfile
if(os.path.isfile("runninghexagons.geojson")):
    os.remove("runninghexagons.geojson")
    print("File Deleted successfully")
else:
    print("File does not exist")

gdf_complete.to_file("runninghexagons.geojson", driver='GeoJSON')

# Plot the original polygons and the intersections
# fig, ax = plt.subplots()
# gdf_complete.plot(ax=ax, color='green', edgecolor='black', alpha=0.7)
# plt.xlabel('Longitude')
# plt.ylabel('Latitude')
# plt.title('RunningHexagons')
# plt.show()

# Move data from new_gpxfiles dir to processed_gpxfiles dir
# gather all files in source folder
allfiles = os.listdir(new_gpx_directory)
 
# iterate on all files to move them to destination folder
for f in allfiles:
    src_path = os.path.join(new_gpx_directory, f)
    dst_path = os.path.join(processed_gpx_directory, f)
    os.rename(src_path, dst_path)

### NOTES
#print(gdf_rh_full.head())
#print(gdf_rh_full.columns.tolist())