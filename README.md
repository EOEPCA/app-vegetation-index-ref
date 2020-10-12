## EOEPCA - Vegetation index using data by reference

[![Build Status](https://travis-ci.com/EOEPCA/app-vegetation-index-ref.svg?branch=master)](https://travis-ci.com/EOEPCA/app-vegetation-index-ref)

### About this application

This is a simple application used as an artifact for testing EOEPCA release 0.3

It validates the fan-out without paradigm where Sentinel-2 acquisitions passed as references to STAC remote items are processed to produce the NBR, NDVI and NDWI vegetation indexes.  

### Build the docker

The repo contains a Dockerfile and a Jenkinsfile.  

The build is done by Terradue's Jenkins instance with the configured job https://build.terradue.com/job/containers/job/eoepca-vegetation-index/

### Create the application package

Run the command below to print the CWL: 

```bash
docker run --rm -it terradue/eoepca-vegetation-index:0.1 vegetation-index-ref-cwl --docker 'terradue/eoepca-vegetation-index-ref:0.1'
```

Save the CWL output to a file called `eoepca-vegetation-index.cwl`

Package it as an application package wrapped in an Atom file with:

```bash
cwl2atom eoepca-vegetation-index-ref.cwl > eoepca-vegetation-index.atom 
```

Post the Atom on the EOEPCA resource manager

### Application execution

Use the parameters:

* **input_reference**:

    * https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191205_0_L2A
    * https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191215_0_L2A

* **aoi**: POLYGON((30.358 29.243,30.358 29.545,30.8 29.545,30.8 29.243,30.358 29.243))
