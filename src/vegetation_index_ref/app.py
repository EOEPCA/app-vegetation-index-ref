import os
import sys
import gdal
import numpy as np
import logging
import click
from pystac import Catalog, Collection, EOItem, MediaType, EOAsset, CatalogType
from shapely.wkt import loads
from time import sleep
import requests
import shutil
from datetime import datetime

gdal.UseExceptions()

logging.basicConfig(stream=sys.stderr, 
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

workflow = dict([('id', 'vegetation-index'),
                ('label', 'Vegetation index'),
                ('doc', 'Vegetation index processor')])


aoi = dict([('id', 'aoi'), 
              ('label', 'Area of interest'),
              ('doc', 'Area of interest in WKT'),
              ('value', 'POLYGON((30.358 29.243,30.358 29.545,30.8 29.545,30.8 29.243,30.358 29.243))'), 
              ('type', 'string')])

input_reference = dict([('id', 'input_reference'), 
                        ('label', 'STAC item for vegetation index'),
                        ('doc', 'STAC item for vegetation index'),
                        ('value', 'https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191205_0_L2A'), 
                        ('type', 'string'),
                        ('scatter', 'True')])

def cog(input_tif, output_tif,no_data=None):
    
    translate_options = gdal.TranslateOptions(gdal.ParseCommandLine('-co TILED=YES ' \
                                                                    '-co COPY_SRC_OVERVIEWS=YES ' \
                                                                    '-co COMPRESS=DEFLATE '))
    
    if no_data != None:
        translate_options = gdal.TranslateOptions(gdal.ParseCommandLine('-co TILED=YES ' \
                                                                        '-co COPY_SRC_OVERVIEWS=YES ' \
                                                                        '-co COMPRESS=DEFLATE '\
                                                                        '-a_nodata {}'.format(no_data)))
    ds = gdal.Open(input_tif, gdal.OF_READONLY)

    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
    ds.BuildOverviews('NEAREST', [2,4,8,16,32])
    
    ds = None

    del(ds)
    
    ds = gdal.Open(input_tif)
    gdal.Translate(output_tif,
                   ds, 
                   options=translate_options)
    ds = None

    del(ds)
    
    os.remove('{}.ovr'.format(input_tif))
    os.remove(input_tif)


@click.command()
@click.option('--input-reference', '-i', 'e_input_reference' , help=input_reference['doc'])
@click.option('--aoi', '-a', 'e_aoi', help=aoi['doc'])
def entry(e_input_reference, e_aoi):

    aoi['value'] = e_aoi
    input_reference['value'] = e_input_reference  
    
    main(input_reference, aoi)

def main(input_reference, aoi):
    
    
    url = input_reference['value']
    
    r = requests.get(url)
    
    # prepare the local STAC catalog
    identifier = r.json()['properties']['sentinel:product_id']
    
    latitude_band = identifier.split('_')[5][3:4]
    grid_square_x = identifier.split('_')[5][4:5]
    grid_square_y = identifier.split('_')[5][5:6]


    properties = {'eo:productType': 'S2MSI2A',
                        'eop:wrsLongitudeGrid': "row['track']",
                        'proj:epsg': r.json()['properties']['proj:epsg'],
                        'eo:cloud_cover': float(r.json()['properties']['eo:cloud_cover']),
                        's2:tile': identifier.split('_')[5],
                        's2:latitude_band': latitude_band,
                        's2:grid_square_x': grid_square_x,
                        's2:grid_square_y': grid_square_y}
    
    bands = [
                {
                    "name": "B01",
                    "common_name": "coastal",
                    "center_wavelength": 0.4439,
                    "full_width_half_max": 0.027
                },
                {
                    "name": "B02",
                    "common_name": "blue",
                    "center_wavelength": 0.4966,
                    "full_width_half_max": 0.098
                },
                {
                    "name": "B03",
                    "common_name": "green",
                    "center_wavelength": 0.56,
                    "full_width_half_max": 0.045
                },
                {
                    "name": "B04",
                    "common_name": "red",
                    "center_wavelength": 0.6645,
                    "full_width_half_max": 0.038
                },
                {
                    "name": "B05",
                    "center_wavelength": 0.7039,
                    "full_width_half_max": 0.019
                },
                {
                    "name": "B06",
                    "center_wavelength": 0.7402,
                    "full_width_half_max": 0.018
                },
                {
                    "name": "B07",
                    "center_wavelength": 0.7825,
                    "full_width_half_max": 0.028
                },
                {
                    "name": "B08",
                    "common_name": "nir",
                    "center_wavelength": 0.8351,
                    "full_width_half_max": 0.145
                },
                {
                    "name": "B8A",
                    "center_wavelength": 0.8648,
                    "full_width_half_max": 0.033
                },
                {
                    "name": "B09",
                    "center_wavelength": 0.945,
                    "full_width_half_max": 0.026
                },
                {
                    "name": "B11",
                    "common_name": "swir16",
                    "center_wavelength": 1.6137,
                    "full_width_half_max": 0.143
                },
                {
                    "name": "B12",
                    "common_name": "swir22",
                    "center_wavelength": 2.22024,
                    "full_width_half_max": 0.242
                }, 
                {
                    "name": "AOT",
                    "center_wavelength": 0,
                    "full_width_half_max": 0
                },
                {
                    "name": "SCL",
                    "center_wavelength": 0,
                    "full_width_half_max": 0
                },
                {
                    "name": "WVP",
                    "center_wavelength": 0,
                    "full_width_half_max": 0
                },
            ]


    item = EOItem(id=identifier,
                   geometry=r.json()['geometry'],
                   bbox=r.json()['bbox'],
                   datetime=datetime.strptime(r.json()['properties']['datetime'], '%Y-%m-%dT%H:%M:%SZ'),
                   properties=properties, 
                   platform='S2B',
                   cloud_cover=float(r.json()['properties']['eo:cloud_cover']),
                   instrument='S2MSI',
                   bands=bands,
                   gsd=[10, 20, 60])
    
    for index, band in enumerate([band['name'] for band in bands]):

        item.add_asset(key=band, 
                    asset=EOAsset(href=r.json()['assets'][band]['href'], 
                                  media_type=MediaType.COG, 
                                  bands=[index]))
    
    catalog = Catalog(id='catalog_id', 
                      description='catalog_description')
    
    catalog.add_item(item)
    
    catalog.normalize_and_save(root_href='instac',
                                  catalog_type=CatalogType.SELF_CONTAINED)
    
    # back to business
    
    bands = [{'name': 'NBR',
              'common_name': 'nbr'}, 
             {'name': 'NDVI',
              'common_name': 'ndvi'},
             {'name': 'NDWI',
              'common_name': 'ndwi'}]
    
    if not 'PREFIX' in os.environ.keys():
    
        os.environ['PREFIX'] = '/opt/anaconda/envs/env_vi'

        os.environ['GDAL_DATA'] =  os.path.join(os.environ['PREFIX'], 'share/gdal')
        os.environ['PROJ_LIB'] = os.path.join(os.environ['PREFIX'], 'share/proj')
        
        
    cat = Catalog.from_file(os.path.join('instac', 'catalog.json')) 
    
    item = next(cat.get_items())
    
    for index, band in enumerate(item.bands):
   
        if band.common_name in ['swir16']:

            asset_swir16 = '/vsicurl/{}'.format(item.assets[band.name].get_absolute_href())

        if band.common_name in ['swir22']:

            asset_swir22 = '/vsicurl/{}'.format(item.assets[band.name].get_absolute_href())

        if band.common_name in ['nir']:

            asset_nir = '/vsicurl/{}'.format(item.assets[band.name].get_absolute_href())

        if band.common_name in ['red']:

            asset_red = '/vsicurl/{}'.format(item.assets[band.name].get_absolute_href())
            
    vrt = '{0}.vrt'.format(item.id)
    
    ds = gdal.BuildVRT(vrt,
                   [asset_red, asset_nir, asset_swir16, asset_swir22],
                   srcNodata=0,
                   xRes=10, 
                   yRes=10,
                   separate=True)

    ds.FlushCache()

    ds = None

    del(ds)
    
    tif = '{0}.tif'.format(item.id)
    
    min_lon, min_lat, max_lon, max_lat = loads(aoi['value']).bounds
    
    gdal.Translate(tif,
                   vrt,
                   outputType=gdal.GDT_Int16,
                   projWin=[min_lon, max_lat, max_lon, min_lat],
                   projWinSRS='EPSG:4326')
    
    os.remove(vrt)
     
        
    # remove STAC local catalog
    shutil.rmtree('instac')   
    
    ds = gdal.Open(tif)
    width = ds.RasterXSize
    height = ds.RasterYSize

    input_geotransform = ds.GetGeoTransform()
    input_georef = ds.GetProjectionRef()
    
    red = ds.GetRasterBand(1).ReadAsArray()
    nir = ds.GetRasterBand(2).ReadAsArray()
    swir16 = ds.GetRasterBand(3).ReadAsArray()
    swir22 = ds.GetRasterBand(4).ReadAsArray()

    ds = None

    del(ds)
    
    nbr = np.zeros((height, width), dtype=np.uint)

    nbr = 10000 * ((nir - swir22) / (nir + swir22))
    
    swir22 = None

    del(swir22)
    
    ndvi = np.zeros((height, width), dtype=np.uint)

    ndvi = 10000 * ((nir - red) / (nir + red))
    
    red = None

    del(red)
    
    ndwi = np.zeros((height, width), dtype=np.uint)

    ndwi = 10000 * ((nir - swir16) / (nir + swir16))
    
    nir = swir16 = None

    del(nir)

    del(swir16)
    
    catalog = Catalog(id='catalog', description='Results')

    catalog.clear_items()
    catalog.clear_children()
    
    item_name = 'INDEX_{}'.format(item.id)
    
    result_item = EOItem(id=item_name,
                         geometry=item.geometry,
                         bbox=item.bbox,
                         datetime=item.datetime,
                         properties={},
                         bands=bands,
                         gsd=10, 
                         platform=item.platform, 
                         instrument=item.instrument)
    
    for index, veg_index in enumerate(['NBR', 'NDVI', 'NDWI']):

        temp_name = '_{}_{}.tif'.format(veg_index, item.id)
        output_name = '{}_{}.tif'.format(veg_index, item.id)

        driver = gdal.GetDriverByName('GTiff')

        output = driver.Create(temp_name, 
                               width, 
                               height, 
                               1, 
                               gdal.GDT_Int16)

        output.SetGeoTransform(input_geotransform)
        output.SetProjection(input_georef)
        output.GetRasterBand(1).WriteArray(nbr),

        output.FlushCache()

        sleep(5)

        output = None

        del(output)

        os.makedirs(os.path.join('stac-results', item_name),
                    exist_ok=True)

        cog(temp_name, os.path.join('stac-results', item_name, output_name))

        result_item.add_asset(key=veg_index.lower(),
                              asset=EOAsset(href='./{}'.format(output_name), 
                              media_type=MediaType.GEOTIFF, 
                              title=bands[index]['name'],
                              bands=bands[index]))
        
    catalog.add_items([result_item])
    
    os.remove(tif)
    
    catalog.normalize_and_save(root_href='stac-results',
                           catalog_type=CatalogType.SELF_CONTAINED)
    
    
if __name__ == '__main__':
    entry()

            

    




