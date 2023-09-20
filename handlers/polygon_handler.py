from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

gdf = gpd.read_file(Path("geo/or_yehuda.shp").resolve())

Jnet_0_gw_id = {
    "1": "0621.1003",
    "2": "0621.1003",
    "3": "0919.2002",
    "4": "0919.2003",
    "5": "0919.2000",
}


def get_getway_id(lon, lat) -> str:
    point = Point(lon, lat)
    print(point)
    gw_df = gdf.query("geometry.contains(@point)")
    gw_index = gw_df["id"].values[0]
    return Jnet_0_gw_id[str(gw_index)]
