[![Project Status: Abandoned – Initial development has started, but there has not yet been a stable, usable release; the project has been abandoned and the author(s) do not intend on continuing development.](https://www.repostatus.org/badges/latest/abandoned.svg)](https://www.repostatus.org/#abandoned)


# EOEPCA - Vegetation index using data by reference

[![Build Status](https://travis-ci.com/EOEPCA/app-vegetation-index-ref.svg?branch=master)](https://travis-ci.com/EOEPCA/app-vegetation-index-ref)

## About this application

This is a simple application used as an artifact for testing EOEPCA release 0.3

It validates the fan-out without paradigm where Sentinel-2 acquisitions passed as references to STAC remote items are processed to produce the NBR, NDVI and NDWI vegetation indexes.  

## Run the application

```bash
cwltool vegetation-index-ref.cwl#vegetation-index-ref vegetation-index-ref.yml 
```

vegetation-index-ref.yml defines the parameters:

* **input_reference**:

    * https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191205_0_L2A
    * https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191215_0_L2A

* **aoi**: POLYGON((30.358 29.243,30.358 29.545,30.8 29.545,30.8 29.243,30.358 29.243))

## Docker container

The repo contains a Dockerfile and a .travis.yml files which builds and pushes to the EOEPCA organization on Dockerhub.  

It can be built manually with:

```bash
docker build . -t vegetation-index-ref:0.1
```

## Create the application package

Package it as an application package wrapped in an Atom file with:

```bash
cwl2atom vegetation-index-ref.cwl > eoepca-vegetation-index-ref.atom 
```

Post the Atom on the EOEPCA resource manager


