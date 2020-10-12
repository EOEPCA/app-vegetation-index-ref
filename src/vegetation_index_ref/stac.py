from pystac import *
from shapely.wkt import loads
from datetime import datetime
import requests

class S2_stac_item():
    
    def __init__(self, s2_stac_item_url):
    
        self.url = s2_stac_item_url
        self.json = self.get_item_json()
        
        self.default_bands = {}

        self.default_bands['B01'] = {
                            "name": "B01",
                            "common_name": "coastal",
                            "center_wavelength": 0.4439,
                            "full_width_half_max": 0.027
                        }


        self.default_bands['B02'] = {
                            "name": "B02",
                            "common_name": "blue",
                            "center_wavelength": 0.4966,
                            "full_width_half_max": 0.098
                        }

        self.default_bands['B03'] =  {
                    "name": "B03",
                    "common_name": "green",
                    "center_wavelength": 0.56,
                    "full_width_half_max": 0.045
                }

        self.default_bands['B04'] =     {
                            "name": "B04",
                            "common_name": "red",
                            "center_wavelength": 0.6645,
                            "full_width_half_max": 0.038
                        }

        self.default_bands['B05'] =    {
                            "name": "B05",
                            "center_wavelength": 0.7039,
                            "full_width_half_max": 0.019
                        }
        self.default_bands['B06'] =   {
                            "name": "B06",
                            "center_wavelength": 0.7402,
                            "full_width_half_max": 0.018
                        }
        self.default_bands['B07'] =   {
                            "name": "B07",
                            "center_wavelength": 0.7825,
                            "full_width_half_max": 0.028
                        }
        self.default_bands['B08'] =    {
                            "name": "B08",
                            "common_name": "nir",
                            "center_wavelength": 0.8351,
                            "full_width_half_max": 0.145
                        }
        self.default_bands['B8A'] =     {
                            "name": "B8A",
                            "center_wavelength": 0.8648,
                            "full_width_half_max": 0.033
                        }
        self.default_bands['B09'] =    {
                            "name": "B09",
                            "center_wavelength": 0.945,
                            "full_width_half_max": 0.026
                        }
        self.default_bands['B11'] =       {
                            "name": "B11",
                            "common_name": "swir16",
                            "center_wavelength": 1.6137,
                            "full_width_half_max": 0.143
                        }
        self.default_bands['B12'] =       {
                            "name": "B12",
                            "common_name": "swir22",
                            "center_wavelength": 2.22024,
                            "full_width_half_max": 0.242
                        }
        self.default_bands['AOT'] =        {
                            "name": "AOT",
                            "center_wavelength": 0,
                            "full_width_half_max": 0
                        }
        self.default_bands['SCL'] =      {
                            "name": "SCL",
                            "center_wavelength": 0,
                            "full_width_half_max": 0
                        }
        self.default_bands['WVP'] =      {
                            "name": "WVP",
                            "center_wavelength": 0,
                            "full_width_half_max": 0
                        }

        
        self.properties =  {'eo:productType': 'S2MSI2A',
                        'eop:wrsLongitudeGrid': "row['track']",
                        'proj:epsg': self.json['properties']['proj:epsg'],
                        'eo:cloud_cover': float(self.json['properties']['eo:cloud_cover']),
                        's2:tile': self.get_identifier().split('_')[5],
                        's2:latitude_band': self.get_identifier().split('_')[5][3:4],
                        's2:grid_square_x': self.get_identifier().split('_')[5][4:5],
                        's2:grid_square_y': self.get_identifier().split('_')[5][5:6]}
        
        

        self.item = self.get_item()
        
        
    def get_item(self):
        
        
        item = Item(id=self.get_identifier(),
                       geometry=self.json['geometry'],
                       bbox=self.json['bbox'],
                       datetime=datetime.strptime(self.json['properties']['datetime'], '%Y-%m-%dT%H:%M:%SZ'),
                       properties=self.properties)
#                       platform=self.get_identifier()[0:2],
#                       cloud_cover=float(self.json['properties']['eo:cloud_cover']),
#                       instrument='S2MSI',
#                       bands=self.bands,
#                       gsd=[10, 20, 60])
        
        eo_item = extensions.eo.EOItemExt(item)
    
        for key in self.default_bands.keys():
            item.add_asset(key=self.default_bands[key]['name'], 
                           asset=Asset(href=self.json['assets'][key]['href'], 
                                       media_type=MediaType.COG))
    
       
        bands = []

        for key, value in item.get_assets().items():

            stac_band = extensions.eo.Band.create(name=self.default_bands[key]['name'], 
                                                  common_name=self.default_bands[key]['common_name'] if 'common_name' in self.default_bands[key].keys() else '',
                                                  description=self.default_bands[key]['name'])
            
            bands.append(stac_band)

            eo_item.set_bands([stac_band], asset=value)
        
        eo_item.set_bands(bands)
          
        eo_item.apply(bands) 
        
        return item
        
    def get_item_json(self):
    
        r = requests.get(self.url)

        if r.status_code == 200:

            return r.json()

        else:

            raise(ValueError)
            
    def get_identifier(self):
    
        return self.json['properties']['sentinel:product_id']