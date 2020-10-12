import os
import sys
import gdal
import numpy as np
import logging
import click
from pystac import * 
from shapely.wkt import loads
from time import sleep
import requests
import shutil
from datetime import datetime
from .stac import S2_stac_item

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
    
    s2_item = S2_stac_item(input_reference['value'])
       
    catalog = Catalog(id='catalog_id', 
                      description='catalog_description')
    
    
    catalog.add_item(s2_item.item)
    
    catalog.normalize_and_save(root_href='instac',
                                  catalog_type=CatalogType.SELF_CONTAINED)
    
    if not 'PREFIX' in os.environ.keys():
    
        os.environ['PREFIX'] = '/opt/anaconda/envs/env_vi'

        os.environ['GDAL_DATA'] =  os.path.join(os.environ['PREFIX'], 'share/gdal')
        os.environ['PROJ_LIB'] = os.path.join(os.environ['PREFIX'], 'share/proj')
        
        
    cat = Catalog.from_file(os.path.join('instac', 'catalog.json')) 
    
    cat.describe()
    
    item = next(cat.get_items())
    
    eo_item = extensions.eo.EOItemExt(item)      
   
    for key in eo_item.item.assets.keys():
   
        if eo_item.item.assets[key].properties['eo:bands'][0]['common_name'] in ['swir16']:
        
             asset_swir16 = '/vsicurl/{}'.format(eo_item.item.assets[key].get_absolute_href())
            
        if eo_item.item.assets[key].properties['eo:bands'][0]['common_name'] in ['swir22']:
        
             asset_swir22 = '/vsicurl/{}'.format(eo_item.item.assets[key].get_absolute_href())

        if eo_item.item.assets[key].properties['eo:bands'][0]['common_name'] in ['nir']:
        
             asset_nir = '/vsicurl/{}'.format(eo_item.item.assets[key].get_absolute_href())
            
        if eo_item.item.assets[key].properties['eo:bands'][0]['common_name'] in ['red']:
        
             asset_red = '/vsicurl/{}'.format(eo_item.item.assets[key].get_absolute_href())
        
            
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
    
    os.remove(tif)
    
    # STAC output
    default_bands = [{'name': 'NBR',
              'common_name': 'nbr'}, 
             {'name': 'NDVI',
              'common_name': 'ndvi'},
             {'name': 'NDWI',
              'common_name': 'ndwi'}]
    
    catalog = Catalog(id='catalog-{}'.format(item.id),
                      description='Results')

    catalog.clear_items()
    catalog.clear_children()
    
    item_name = 'INDEX_{}'.format(item.id)
    
    
    item.properties.pop('eo:bands', None)
    item.properties['eo:gsd'] = 10
    item.properties['eo:platform'] = ['sentinel-2']
    item.properties['eo:instrument'] = 'MSI'
    
    result_item = Item(id=item_name,
                       geometry=item.geometry,
                       bbox=item.bbox,
                       datetime=item.datetime,
                       properties=item.properties)
    
    result_item.common_metadata.set_gsd(10)
    
    eo_item = extensions.eo.EOItemExt(result_item)
    
    #eo_item.set_bands(bands)
    
    #eo_item.common_metadata.set_gsd(10)

                     #                     result_item = EOItem(id=item_name,
                     #    geometry=item.geometry,
                     #    bbox=item.bbox,
                     ##    datetime=item.datetime,
                     #    properties={},
                     #    bands=bands,
                     #    gsd=10, 
                     #    platform=item.platform, 
                     #    instrument=item.instrument)
    bands = []
    
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

        os.makedirs(os.path.join('.', item_name),
                    exist_ok=True)

        cog(temp_name, os.path.join('.', item_name, output_name))

        result_item.add_asset(key=veg_index.lower(),
                           asset=Asset(href='./{}'.format(output_name), 
                                       media_type=MediaType.GEOTIFF))
        
        asset = result_item.get_assets()[veg_index.lower()]                                   
         
        #description = bands[index]['name']
            
        stac_band = extensions.eo.Band.create(name=veg_index.lower(), 
                                                   common_name=default_bands[index]['common_name'],
                                                   description=default_bands[index]['name'])
        bands.append(stac_band)
            
        eo_item.set_bands([stac_band], asset=asset)
    
    eo_item.set_bands(bands)
          
    eo_item.apply(bands)    
    
        #result_item.add_asset(key=veg_index.lower(),
        #                      asset=EOAsset(href='./{}'.format(output_name), 
        #                      media_type=MediaType.GEOTIFF, 
        #                      title=bands[index]['name'],
        #                      bands=[bands[index]]))
        
    catalog.add_items([result_item])
    
    catalog.normalize_and_save(root_href='./',
                               catalog_type=CatalogType.SELF_CONTAINED)
    
    
    
if __name__ == '__main__':
    entry()

            

    




