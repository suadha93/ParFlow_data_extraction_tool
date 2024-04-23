


""" This module contains three functions designed to extract variables
from the ParFlowCLM DE06 domain. The first function 
locates the lower boundary layer containing the specified depth. 
the second function extracts a time series for a specific location
and writes it in an ASCII file. The third function has similar functionality
to the function before, but it returns the variable for the location for all depths.
"""



import numpy as np
from netCDF4 import Dataset
import datetime
import csv
import json


def spher_dist( lon1, lat1, lon2, lat2, Rearth=6371):
    """ calculate the spherical / haversine distance

    Source: https://www.kompf.de/gps/distcalc.html
    This function is supposed to proper handle different shaped coords
    latX and lonX is supposed to be passed in rad. 
    This function was originally written Niklas WAGNER 
    for SLOTH (https://hpscterrsys.github.io/SLOTH/README.html)

    Parameters
    ----------
    lon1 : ndarray
        Longitude value in [rad] of first point in [rad]. Could be any dim
    lat1 : ndarray
        Latitude value in [rad] of first point in [rad]. Could be any dim
    lon2 : ndarray
        Longitude value in [rad] of second point in [rad]. Could be any dim
    lat2 : ndarray
        Latitude value in [rad] of second point in [rad]. Could be any dim
    Rearth : int or float
        The earth radius.

    Returns
    -------
    ndarray
        The distance is returned

    Notes
    -----
    Source: https://www.kompf.de/gps/distcalc.html

    """
    term1 = np.sin(lat1) * np.sin(lat2)
    term2 = np.cos(lat1) * np.cos(lat2)
    term3 = np.cos(lon2 - lon1)
#    print(Rearth * np.arccos(term1 + term2 * term3))

    return Rearth * np.arccos(term1+term2*term3)


def find_depth_index(depth):

    """ Find the lower boundary of the layer where the inserted depth is within.
    
    Parameters
    ----------
    depth : float
       soil depth in [meters]

    Returns
    -------
    float
      the lower boundary depth is returned in [meters]
       
    Notes
    -----
    The simulations are calculated for 15 layers from 
    the surface to 60m depth in mm water column
    each depth represents the lower boundary of the layer.
    This function will find out which layer is 
    the depth inserted is within and then returns
    the lower boundary of the layer

   """

    depth_list = [60.0, 42.0, 27.0, 17.0, 7.0, 3.0, 2.0, 1.3, 0.8, 0.5, 0.3,
                  0.17, 0.1, 0.05, 0.02]
   
   #if the depth is the lower boundary of the layer
    try:
        index = depth_list.index(depth)
        print(index)
        return index

    #if the depth is within a layer, find the layer boundaries which
    #the depth falls in between
    except ValueError:
        
        lower_boundary = None
        higher_boundary = None

        for i in range(len(depth_list) - 1):
            if depth_list[i] >= depth > depth_list[i + 1]:
                higher_boundary = depth_list[i + 1]
                lower_boundary = depth_list[i]
                depth_n = lower_boundary
                break
        index_n = depth_list.index(depth_n)

        return index_n,depth_n


def data_extraction_csv(data_input,lls_indicators):
    
    """ extract a time-series for a desired time 
    period for a specific location 
    and a specific depth
    
    Parameters
    ----------
    
    data_input : json file 

    Returns
    ------
    csv file
    """

    #extracts infromation from the json file were the input information is provided

    with open(data_input, 'r') as f:
        locations = json.load(f)
        for location in locations:
            stationID = location["stationID"]
            stationLat = location["stationLat"]
            stationLon = location["stationLon"]
            fncdata = location["ParFlowData"]
            depth = location['Depth']
            print(f'Location: {stationID}')
            
            #finding the index of the Lon and Lat in interest
            with Dataset(fncdata, 'r') as nc:
            
                SimLons=nc.variables['lon'][:]
                SimLats=nc.variables['lat'][:]

            dist = spher_dist(np.deg2rad(SimLons),np.deg2rad(SimLats),np.deg2rad(stationLon),np.deg2rad(stationLat)) 

            mapped_idx = np.unravel_index(np.argmin(dist, axis=None), dist.shape)
            MapYIdx = mapped_idx[0]
            MapXIdx = mapped_idx[1]

            print(f'Found:')
            print(f'Mapped x index: {MapXIdx}')
            print(f'Mapped y index: {MapYIdx}')

            #extract the infromation for the soil layers and determine whether 
            #the point in interest is located directly in a water body such as rivers, lakes or seas
            with Dataset(lls_indicators, 'r') as ncIndicator: 
               indicator_value = ncIndicator.variables['Indicator'][0,14,MapYIdx,MapXIdx]
                  
            # Check if the location falls dierectly on a river, lake or sea
            if indicator_value in [19,20, 21]:

            # Find the indices that would sort the distances array in ascending order
              sorted_indices = np.argsort(dist, axis=None)
        
            # Convert the 1D indices to 2D indices
              sorted_indices_2d = np.unravel_index(sorted_indices, dist.shape)

            #Get the first 9 indices, which correspond to the closest distances
              closest_indices_9 = list(zip(sorted_indices_2d[0][1:10], sorted_indices_2d[1][1:10]))
              lons_to_add = []
              lats_to_add = []
            # test if the other nearest neighbours are on a river, lake, sea
              for i in range(len(closest_indices_9)):
                  with Dataset(lls_indicators, 'r') as ncIndicator:
                       indicator_value = ncIndicator.variables['Indicator'][0,14,sorted_indices_2d[0][i],sorted_indices_2d[1][i]]
                       
                       if indicator_value not in [19,20,21]:
                          lon_n9 = ncIndicator.variables['lon'][sorted_indices_2d[0][i],sorted_indices_2d[1][i]]
                          lon_n9 = lon_n9.item()
                          lons_to_add.append(lon_n9)
                          lat_n9 = ncIndicator.variables['lat'][sorted_indices_2d[0][i],sorted_indices_2d[1][i]]
                          lat_n9 = lat_n9.item()
                          lats_to_add.append(lat_n9)
              if not lons_to_add:
                  print("The chosen location is located directly on a lake, river or sea, please insert a different location.")
                  break

              print("The chosen location is located directly on a lake, river or sea, here are other suggested location/locations:")
              for n in range(len(lats_to_add)):
                    latitude = "{:.5f}".format(lats_to_add[n])
                    longitude = "{:.5f}".format(lons_to_add[n])
                    print(f"Latitude: {latitude}, Longitude: {longitude}")
                    break
            
            # if the condition passed, the next line will find the lowest boundary 
            # of the depth in question
            else:
                depth_index,depth_n = find_depth_index(depth)
            
            # extract the data of the variable from the netcdf file
                with Dataset(fncdata, 'r') as nc:
                    variables = nc.variables.keys()
                    variable = list(variables)[-1]
                    var=nc.variables[variable][:,depth_index,MapYIdx,MapXIdx]
                    unit = nc.variables[variable]
                    unit = unit.units
                    variable_long_name = nc.variables[variable].long_name
                    dates = nc.variables['time'][:]
                print(f'data for Lat:{stationLat}, Lon:{stationLon} is extracted and being written in a CSV file')
                startDate_hr = dates[0]
                reference_startDate = datetime.datetime(1901, 1, 1)
                readable_startDate = reference_startDate + datetime.timedelta(hours=float(startDate_hr))
                startDate = readable_startDate.strftime("%Y%m%d")

                endDate_hr = dates[-1]
                reference_endDate = datetime.datetime(1901, 1, 1)
                readable_endDate = reference_endDate + datetime.timedelta(hours=float(endDate_hr))
                endDate =readable_endDate.strftime("%Y%m%d")

                #open an CSV and save the time series
                nameCSV = f'Station_{stationID[0]}_ADAPTER_DE05_ECMWF-HRES-forecast_FZJ-IBG3-ParFlowCLM380_v04aJuwelsGpuProd_{variable}_{depth_n}m-depth_{startDate}-{endDate}.csv'
                today_date = datetime.datetime.today().strftime('%Y-%m-%d')
               
                fCSV = open(nameCSV, 'w', newline='')
                writer = csv.writer(fCSV)
                writer.writerow(['stationID:',f'{stationID[0]}'])
                writer.writerow(['stationLat:',f'{stationLat}'])
                writer.writerow(['stationLon:',f'{stationLon}'])
                writer.writerow(['Parameter:',variable_long_name])
                writer.writerow(['Unit:',unit])
                writer.writerow(['Time aggregation:','daily'])
                writer.writerow(['Depth:',f'{depth_n} m'])
                writer.writerow(['Model simulation:','ParFlow/CLM DE05_domain 611m resolution'])
                writer.writerow(['Atmospheric forcing:','ECMWF HRES daily deterministic forecast 0-24h'])
                writer.writerow(['Institution:','Forschungszentrum Juelich IBG-3'])
                writer.writerow(['Time series extracted on:', today_date])
                writer.writerow([''])
                
                #dayDate = startDate
                dayDate = datetime.datetime.strptime(startDate,"%Y%m%d")
                dayDate = dayDate.replace(hour=12, minute=0, second=0)

                for dd in range(len(dates)):
                    date_value = dates[dd]
                    reference_date = datetime.datetime(1901, 1, 1)
                    readable_date = reference_date + datetime.timedelta(hours=float(date_value))
                    dayDate = readable_date.replace(hour=12, minute=0, second=0)
                    var1Drow = [f'{dayDate}']

                    var1Drow.append(var[dd])

                    writer.writerow(var1Drow)


                fCSV.close()

                print('csv file saved')

def data_extraction_variable(data_input,llsmask):

    """ returns a variable of a desired time period for a specific location
    for the 15 available layers.
        
        Parameters
        ----------
        data_input: json file
        llsmask: netcdf file

        Returns
        -------
        Variable
    """


    #extracts infromation from the json file were the input information is provided

    with open(data_input, 'r') as f:
        locations = json.load(f)
        for location in locations:
            stationID = location["stationID"]
            stationLat = location["stationLat"]
            stationLon = location["stationLon"]
            fncdata = location["ParFlowData"]

    #finding the index of the Lon and Lat in interest

            with Dataset(fncdata, 'r') as nc:

                SimLons=nc.variables['lon'][:]
                SimLats=nc.variables['lat'][:]

            dist = spher_dist(np.deg2rad(SimLons),np.deg2rad(SimLats),np.deg2rad(stationLon),np.deg2rad(stationLat))
            mapped_idx = np.unravel_index(np.argmin(dist, axis=None), dist.shape)
            MapYIdx = mapped_idx[0]
            MapXIdx = mapped_idx[1]

            print(f'Found:')
            print(f'Mapped x index: {MapXIdx}')
            print(f'Mapped y index: {MapYIdx}')

            #extract the infromation for the soil layers and determine whether 
            #the point in interest is located directly in a water body such as rivers, lakes or seas
            with Dataset(lls_indicators, 'r') as ncIndicator: 
               indicator_value = ncIndicator.variables['Indicator'][0,14,MapYIdx,MapXIdx]
                  
            # Check if the location falls dierectly on a river, lake or sea
            if indicator_value in [19,20, 21]:

            # Find the indices that would sort the distances array in ascending order
              sorted_indices = np.argsort(dist, axis=None)
        
            # Convert the 1D indices to 2D indices
              sorted_indices_2d = np.unravel_index(sorted_indices, dist.shape)

            #Get the first 9 indices, which correspond to the closest distances
              closest_indices_9 = list(zip(sorted_indices_2d[0][1:10], sorted_indices_2d[1][1:10]))
              lons_to_add = []
              lats_to_add = []
            # test if the other nearest neighbours are on a river, lake, sea
              for i in range(len(closest_indices_9)):
                  with Dataset(lls_indicators, 'r') as ncIndicator:
                       indicator_value = ncIndicator.variables['Indicator'][0,14,sorted_indices_2d[0][i],sorted_indices_2d[1][i]]
                       
                       if indicator_value not in [19,20,21]:
                          lon_n9 = ncIndicator.variables['lon'][sorted_indices_2d[0][i],sorted_indices_2d[1][i]]
                          lon_n9 = lon_n9.item()
                          lons_to_add.append(lon_n9)
                          lat_n9 = ncIndicator.variables['lat'][sorted_indices_2d[0][i],sorted_indices_2d[1][i]]
                          lat_n9 = lat_n9.item()
                          lats_to_add.append(lat_n9)
              if not lons_to_add:
                  print("The chosen location is located directly on a lake, river or sea, please insert a different location.")
                  break

              print("Here are other suggested location/locations:")
              for n in range(len(lats_to_add)):
                    latitude = "{:.5f}".format(lats_to_add[n])
                    longitude = "{:.5f}".format(lons_to_add[n])
                    print(f"Latitude: {latitude}, Longitude: {longitude}")
                    break
            # if the condition passed, the next line will find the lowest boundary 
            # of the depth in question

            else:
                with Dataset(fncdata, 'r') as nc:
                    variables = nc.variables.keys()
                    variable = list(variables)[-1]
                    var=nc.variables[variable][:,:,MapYIdx,MapXIdx]
                print(f'data for Lat:{stationLat}, Lon:{stationLon} is extracted')
                return var


def test(data_input,lls_indicators):

    var = data_extraction_variable(data_input,lls_indicators)
    print(var)




if __name__ == "__main__":

    data_input="/p/project/pfgpude05/hammoudeh1/ParflowCLM_postpro_scripts/data_extraction/data_input_example_1.json"
    lls_indicators = '/p/project/pfgpude05/hammoudeh1/ParflowCLM_postpro_scripts/data_extraction/DE-0055_INDICATOR_regridded_rescaled_SoilGrids250-v2017_BGRvector_newAllv.nc'
    data_extraction_csv(data_input,lls_indicators)
   # test(data_input,lls_indicators)
