import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
gdf = gpd.read_file("or_yehuda.shp")
Jnet_0_gw_id = {
    "1": '0621.1003',
    "2": '0621.1003',
    "3": '0919.2002',
    "4": '0919.2003',
    "5": '0919.2000',
}
def get_getway_id(lon, lat) -> str:
    # Load your polygon data, replace 'your_polygon_data.shp' with your file
    # Find the polygon id that contains the point
    point = Point(lon, lat)
    gw_df = gdf.query("geometry.contains(@point)")
    gw_index = gw_df['id'].values[0]
    return Jnet_0_gw_id[str(gw_index)]
# Print the polygon id
print(get_getway_id(lon=34.872224, lat=32.027169))

