# Running Hexagons

#https://stackoverflow.com/questions/54726758/merging-multiple-gpx-files-into-a-single-gpx-file-with-multiple-tracks

library(rgdal)
library(leaflet)
library(dplyr)
library(sf)
library(geojsonsf)
library(htmlwidgets)

workingdir <- dirname(rstudioapi::getSourceEditorContext()$path)
datadir <- paste0(workingdir, "/data")
hexagonfile <- paste0(workingdir, "/hexagonNetherlands.json")

# List of GPX-file
files <- list.files(datadir, pattern = "*.gpx", full.names=T)

# Read hexagons of the Netherlands
hexagons <- geojson_sf(hexagonfile)

# Init sf with 1 first GPX file
firstGPXfile <- files[1]

#gpx <- readOGR(dsn=firstGPXfile, layer="tracks") 
gpx <- st_read(dsn=firstGPXfile, layer="tracks") 
gpx_sf <- st_as_sf(gpx)
gpx_sf <- gpx_sf[c(1)] # keep first column
df_runninghexagon <- st_join(gpx_sf, hexagons)

# Read rest of GPX files and append to df
restofGPXfiles <- files[-1]

for (f in restofGPXfiles) {
  #gpx <- readOGR(dsn=f, layer="tracks") 
  gpx <- st_read(dsn=f, layer="tracks") 
  gpx_sf <- st_as_sf(gpx)
  gpx_sf <- gpx_sf[c(1)]
  gpx_sf <- rbind(gpx_sf,gpx_sf[c(1)])
  df_runninghexagon <- rbind(df_runninghexagon, st_join(gpx_sf, hexagons))
}


df_runninghexagons <- df_runninghexagon %>%
  filter(substr(name,1,7)=="Running") %>%
  filter(!is.na(uuid))

df_runninghexagons$name <- as.vector(df_runninghexagons$name)
df_runninghexagons$name <- substr(df_runninghexagons$name,1,nchar(df_runninghexagons$name)-8)
df_runninghexagons$name_uuid <- paste(df_runninghexagons$name, df_runninghexagons$uuid, sep = "_")


# Count number of runs per hexagons
countRunsPerHexagon <- df_runninghexagons[!duplicated(df_runninghexagons$name_uuid),] 

df_countRunsPerHexagon <- as.data.frame(countRunsPerHexagon) %>%
  select(c(name,uuid)) %>%
  group_by(uuid) %>%
  summarise(count = n())  %>%
  as.data.frame() # Convert spatial frame to dataframe in order to merge data

# Find first run in specific hexagon
df_firstRun <- 
  df_runninghexagons[!duplicated(df_runninghexagons$uuid),] %>%
  select(c(name,uuid)) %>%
  as.data.frame() # Convert spatial frame to dataframe in order to merge data

# Merge countRuns and firstRun
runningHexagons <- merge(df_countRunsPerHexagon, df_firstRun, by = "uuid", all=TRUE)

# Add geometry
runningHexagons <- left_join(runningHexagons, hexagons, by = "uuid")
st_geometry(runningHexagons) <- runningHexagons$geometry.y

#runningHexagons <- merge(hexagons, runningHexagons, by.x = "uuid", by.y = "uuid", all=FALSE)
#runningHexagons <- st_as_sf(runningHexagons)

runningHexagons <- select(runningHexagons, c(name, count))

# Define bbox
bbox <- st_bbox(runningHexagons) # current bounding box
xrange <- bbox$xmax - bbox$xmin # range of x values
yrange <- bbox$ymax - bbox$ymin # range of y values
bbox[1] <- bbox[1] - (0.5 * xrange) # xmin - left
bbox[3] <- bbox[3] + (0.5 * xrange) # xmax - right
bbox[2] <- bbox[2] - (0.5 * yrange) # ymin - bottom
bbox[4] <- bbox[4] + (0.5 * yrange) # ymax - top

# Create a continuous palette function
pal <- colorNumeric(
  palette = "BuPu",
  n = 5,
  domain = runningHexagons$count
)

pal <- colorBin(
  palette = "BuPu",
  domain,
  bins = 5
)

indexfile <- 
leaflet(runningHexagons, 
        options = leafletOptions(
          zoomControl = FALSE
        )
) %>% 
  setView(lng = 5, lat = 52.833, zoom = 8) %>%
  #fitBounds(~min(long), ~min(lat), ~max(long), ~max(lat)) %>%
  fitBounds(
    lng1 = min(bbox$xmin),
    lat1 = min(bbox$ymin),
    lng2 = max(bbox$xmax),
    lat2 = min(bbox$ymax)
    #options = list(padding = c(2,2))
  ) %>%
  # Base groups
  addTiles(group = "OSM") %>%
  addProviderTiles(providers$Stamen.Toner, group = "Toner") %>%
  addProviderTiles(providers$Stamen.TonerLite, group = "Toner Lite") %>%
  addPolygons(
    fillColor = ~colorBin('BuPu',count, 4)(count),
    #color = "#444444", 
    weight = 1, 
    smoothFactor = 0.5,
    opacity = 1.0, 
    fillOpacity = 0.5,
    popup = paste("<b>First run: </b>", runningHexagons$name, "<br>", "<b>Number of runs: </b>", runningHexagons$count),
    highlightOptions = highlightOptions(color = "white", 
                                        weight = 2,
                                        bringToFront = TRUE),
    group = "Hexagons"
  ) %>%
  # Layers control
  addLayersControl(
    baseGroups = c("OSM", "Toner", "Toner Lite"),
    overlayGroups = c("Hexagons"),
    options = layersControlOptions(collapsed = FALSE)
  ) %>%
  addLegend(
    position = "bottomleft",
    pal = colorBin('BuPu', runningHexagons$count, 4),
    values = runningHexagons$count,
    title = "Number of Runs") %>%
  
  addControl(paste("<h3> Running Hexagons </h3>", "There are 65021 hexagons in <br> the Netherlands. <br> I ran in ",  "<b>", nrow(runningHexagons), "</b> hexagons." ), position = "topleft")


indexfile

# Save HTML-file
saveWidget(indexfile, "index.html")
