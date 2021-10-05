"""Helper functions for wrapper in raster_statistics"""

import math
from pathlib import Path 
import geopandas as gpd
import numpy as np
import pandas as pd 
import rasterio

def generate_tiles(raster, zone_raster):
    """
    Generator that yields each tile in both input rasters as numpy arrays.
    
    ********************
    NB: Both rasters should have same dimensions, resolution and transform
    *********************

    Parameters:
    -----------
    raster  :   (Path/str)
        Path to input raster for

    zone_raster :   (Path/str)
        Path to raster defining zones

    Returns:
    --------
    data :  (np.ndarray)
        Array representing pixels of tile in raster

    zones   :   (np.ndarray)
        Array representing respective zones of pixels in zone_raster
    """
    with rasterio.open(raster) as src, rasterio.open(zone_raster) as zon:
        for ij, window in src.block_windows(1):
            data = src.read(window=window).astype(np.float32)
            if not np.all(data) == src.nodata:
                zones = zon.read(window=window)
                yield data, zones


def get_unique_units(zones, nodata=None):
    """
    Returns a list of unique values in numpy arrays. If nodata is set with an integer, this will be removed from the list

    Parameters:
    ------------
    zones   :   (np.ndarray)
        Array of zone codes in tile of raster

    nodata  :   (None/list)
        Nodata value(s) to be removed from array. Default = None

    Returns:
    ----------
    unique_zones    :   (list)
        List of unique values in zones array without nodata values 

    """
    zones_unique = list(np.unique(zones))
    if nodata:
      [zones_unique.remove(x) for x in nodata if x in zones_unique]
    return zones_unique

def make_df_for_unique_zones_in_array(raster, zone_raster, stats='sum', nodata=None):
    """
    Returns pandas dataframe for statistic of each admin unit. Stats to be specified in a list are:
        sum
        count
        mean
        min
        max 
        standard deviation (std)

    Parameters:
    ------------
    raster  :   (Path/str)
        Input raster 

    zone_raster :   (Path/str)
        Zone Raster

    stats   :   (str/list)
        String with individual stats separated by space OR list of strings of stats to calculate (i.e. "sum mean max" OR ["sum", "mean", "max"])

    nodata  :   (int)
        Nodata value used to mask

    Returns
    --------
    stats_df    :   (pd.DataFrame)
        Dataframe of statistics chosen
    """
    stats_dict, stats_list = make_empty_dict(stats)
    for data, zones in generate_tiles(raster, zone_raster):
        for admin_unit in get_unique_units(zones, nodata=nodata):
            stats_dict['ADMINID'].append(admin_unit)
            stats_dict['sum'].append(np.sum(data, where=zones==admin_unit))
            stats_dict['sum_x2'].append(np.sum(data**2, where=zones==admin_unit))
            if "count" in stats_list:
                stats_dict['count'].append(len(data[zones == admin_unit].flatten()))
            if "min" in stats_list:
                stats_dict['min'].append(data[zones == admin_unit].min())
            if "max" in stats_list:
                stats_dict['max'].append(data[zones == admin_unit].max())
    cols_dict = {x:x for x in stats_list if not x in ['mean', 'std']} #these columns will be inserted later
    cols_dict['sum_x2'] = 'sum'     
    holder_df = pd.DataFrame(data=stats_dict)
    if 'count' in stats_list:
        cols_dict['count'] = 'sum'
    df = holder_df.groupby(['ADMINID'])[['sum', 'min', 'max', 'count', 'sum_x2']].agg(cols_dict)
    #df = holder_df.copy()
    print(df)
    if 'mean' in stats_list:
        df['mean'] = df['sum'] / df['count']
    if 'std' in stats_list:
        df['std'] = df.apply(lambda x: calc_std(x['sum'], x['sum_x2'], x['count'], x['mean']), axis=1)
    return df

def calc_std(sum_, sum_x2, count, mean):
    """
    Return std deviation
    """
    try:
        mean_x2 = mean **2
        data_x2_mean = sum_x2/count
        variance = data_x2_mean - mean_x2
        print(f'++++++++++++++++{variance}')
        print(f'SQUARED MEAN {mean_x2}')
        print(f'MEAN {mean}')
        print(f'SUM OF SQUARES {sum_x2}')
        print(f'COUNT {count}')
        std = math.sqrt(sum_x2/count - mean_x2)
        print(f'STD {std}')
    except ValueError:
        std = 0
    return std
    

def make_empty_dict(stats="sum"):
    """
    Makes an empty dict with keys for ADMINID and requested stats with an empty list as the values

    Parameters:
    -----------

    stats : (list/str)
      String with individual stats separated by space OR list of strings of stats to calculate (i.e. "sum mean max" OR ["sum", "mean", "max"])

    Returns:
    --------
    empty_dict :    (dict)
        Dictionary with keys for each of the stats and ADMINID and an empty list for each

    stats_list  : (list)
        Converts stats to a list
    """
    if isinstance(stats, str):
        stats = stats.split(" ")
    empty_dict = {'ADMINID': []}
    for i in stats:
        if not i in ["mean", "std"]: #These columns will be added later
            empty_dict[i] = []
    empty_dict['sum_x2'] = [] #Container for sum of squares
    return empty_dict, stats
