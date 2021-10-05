"""Unit tests for utils.py"""

import pytest 

import numpy as np
import pandas as pd
from pathlib import Path 

from wpZonalStatisticsPy import generate_tiles, get_unique_units, make_empty_dict, make_df_for_unique_zones_in_array
BASE = Path(__file__).resolve().parent.joinpath('data')

#--------INPUT------------#
RASTER = BASE.joinpath('ABW/abw_px_area_100m.tif')
ZONES = BASE.joinpath('ABW/abw_subnational_admin_2000_2020.tif')

RASTER_BIG = BASE.joinpath('BTN/btn_px_area_100m.tif')
ZONES_BIG = BASE.joinpath('BTN/BTN_subnational_admin_2000_2020.tif')
#--------INPUT------------#

#--------OUTPUT------------#
ZONALS = BASE.joinpath('ABW/test_abw_zonals.csv')
SHP = BASE.joinpath('ABW/test_abw_shp.shp')
#--------OUTPUT------------#

def test_generate_tiles():
    generator_function = generate_tiles(RASTER, ZONES)
    data, zones = next(generator_function)
    assert isinstance(data, np.ndarray)
    assert isinstance(zones, np.ndarray)
    assert data.shape == zones.shape

def test_get_unique_units():
    zones = np.array([[1,2,3], [4,5,6], [4,5,6], [1,2,3]], np.int16)
    nodata = [5,6]
    zones_unique = get_unique_units(zones, nodata=nodata)
    assert zones_unique == [1,2,3,4]

def test_make_empty_dict():
    stats = ["sum", "mean", "max"]
    empty_dict, stats_list = make_empty_dict(stats)
    assert stats_list == stats
    assert empty_dict == {"ADMINID": [], "sum": [], "mean": [], "max": []}
    empty_dict_2, stats_list2 = make_empty_dict()
    assert len(stats_list2) == 1
    assert empty_dict_2 == {"ADMINID": [], "sum": []}

def test_make_df_for_unique_zones_in_array():
    stats_dict = make_df_for_unique_zones_in_array(RASTER, ZONES, stats="sum count min max", nodata=[8888])
    assert isinstance(stats_dict, pd.DataFrame)
    assert 'count' in stats_dict.keys()

def test_make_df_for_unique_zones_in_array_BIG():
    stats_df = make_df_for_unique_zones_in_array(RASTER_BIG, ZONES_BIG, stats="sum count min max mean std", nodata=[8888])
    print(stats_df.head())
    stats_df.to_csv(BASE.joinpath('TEST.csv'))
    assert isinstance(stats_df, pd.DataFrame)
    assert 'count' in stats_df.columns

