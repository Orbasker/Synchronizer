import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
# Load your polygon data, replace 'your_polygon_data.shp' with your file
gdf = gpd.read_file('Jnet_0_gws.shp')

# Plot the polygons
plt.figure(figsize=(10, 10))
gdf.plot(color='red')

# Add a point to the plot
plt.plot([34.8567], [32.0232], marker='o', color='blue', markersize=15)

# Add a label to the point
# plt.annotate('Point', xy=[34.8567, 32.0232], ha='center', va='center')

# Add a title and a legend to the plot
# plt.title('Polygons with Point')
# plt.legend()
plt.show()

point = Point(34.8567, 32.0232)
in_polygon = point.within(gdf['geometry'])
# save the true index if exist
for index in range(len(in_polygon)):
    if in_polygon[index]:
        gw_id = index   
# print the result
print("index:")
print(gw_id+1)
print("result:")
print(in_polygon)

