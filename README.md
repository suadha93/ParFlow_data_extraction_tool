# Welcome to the ParFlowCLM DE06 extraction tool

This repository includes scripts and examples to extract time-series or variables for a specific location from ParFlowCLM DE06 simulations (https://adapter-projekt.org/). Selected variables are available on THREDDS-server (https://service.tereno.net/thredds/catalog/forecastnrw/products/catalog.html). 

This tool is designed to be able to exract information from ParFlowCLM DE06 for a location without having to download the data.

## Getting Started

### Prepare the repository for the extraction tool

Clone the repository as usual

``` bash
git clone https://icg4geo.icg.kfa-juelich.de/SoftwareTools/parflowclm_de06_data_extraction_tool.git
```


### Notes

- The simulations are calculated for 15 layers from the surface to 60m depth in mm water column each depth represents the lower boundary of the layer, their thickness varies with depth. The depths (in meters) are available as follows: 60.0, 42.0, 27.0, 17.0, 7.0, 3.0, 2.0, 1.3, 0.8, 0.5, 0.3,0.17, 0.1, 0.05, 0.02. If the depth inserted as input falls between two layer, the data extracted will be for the lower boundary of the layer. 
