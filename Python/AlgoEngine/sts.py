import numpy as np
from math import acos
from AlgoEngine.utils import getVolume


def getSTSHistogram(ptv_roi_block, oar_roi_block, n_bins):
    """
    Creates the vectors for an STS histogram. 

    Parameters
    ----------
    ptv_roi_block : 3d Ndarray
        A 3D array of dimensions h x w  x num_cts. 
        Contains 1s on and inside PTV contour perimeter and 0s elsewhere.

    oar_roi_block : 3d Ndarray
        A 3D array of dimensions h x w  x num_cts. 
        Contains 1s on and inside OAR contour perimeter and 0s elsewhere.

    n_bins : int
        Number of bins to use in histogram. 

    Returns
    -------
    elevation_bins : 1D NdArray
        Intervals for elevation which each value falls into. Length is `n_bins`.

    distance_bins : 1D NdArray
        Intervals for distance which each value falls into. Length is `n_bins`.

    azimuth_bins : 1D NdArray
        Intervals for azimuth which each value falls into. Length is `n_bins`.

    amounts : 3D NdArray
        Dimensions are [elevation_bins, distance_bins, azimuth_bins]. Contains
        percentage of points in each interval, normalized but not cumulative.

    amounts : 3D NdArray
        Cumulative amounts. Dimensions are [elevation_bins, distance_bins, azimuth_bins]. Contains
        percentage of points in each interval, normalized and cumulative.

    """
    centroid = getCentroid(oar_roi_block)
    
    elevation = np.zeros(np.count_nonzero(ptv_roi_block))
    distance = np.zeros(np.count_nonzero(ptv_roi_block))
    azimuth = np.zeros(np.count_nonzero(ptv_roi_block))
    
    count = 0

    for i in range(0, ptv_roi_block.shape[0]):
        for j in range(0, ptv_roi_block.shape[1]):
            for k in range(0, ptv_roi_block.shape[2]):
                if ptv_roi_block[i,j,k] == 1:
                    elevation[count] = getElevation(centroid, [i,j,k])
                    distance[count] = getDistance(centroid, [i,j,k])
                    azimuth[count] = getAzimuth(centroid, [i,j,k])
                    count += 1

    epsilon = 1e-6 # To guarantee max > any point in array

    elevation_max = np.max(elevation) + epsilon
    elevation_min = np.min(elevation)
    distance_max = np.max(distance) + epsilon
    distance_min = np.min(distance) 
    azimuth_max = np.max(azimuth) + epsilon
    azimuth_min = np.min(azimuth) 

    elevation_delta = (elevation_max-elevation_min) / n_bins
    distance_delta = (distance_max-distance_min) / n_bins
    azimuth_delta = (azimuth_max-azimuth_min) / n_bins

    elevation_bins = np.concatenate((np.arange(elevation_min,elevation_max,elevation_delta), 
                                 np.expand_dims(np.array(elevation_max), axis=0)))
    distance_bins = np.concatenate((np.arange(distance_min,distance_max,distance_delta), 
                                    np.expand_dims(np.array(distance_max), axis=0)))
    azimuth_bins = np.concatenate((np.arange(azimuth_min,azimuth_max,azimuth_delta), 
                                   np.expand_dims(np.array(azimuth_max), axis=0)))
    amounts = np.zeros((elevation.shape[0], 4)).astype(np.float32)
    
    amount = 0.0
    count = 0

    for i in range(0, elevation_bins.shape[0] - 1):
        for j in range(0, distance_bins.shape[0] - 1):
            for k in range(0, azimuth_bins.shape[0] - 1):
                amount = np.count_nonzero((elevation >= elevation_bins[i]) & 
                    (elevation < elevation_bins[i+1]) & (distance >= distance_bins[j]) 
                    & (distance < distance_bins[j+1]) & (azimuth >= azimuth_bins[k]) & 
                    (azimuth < azimuth_bins[k+1]))
                amounts[count] = np.array([elevation_bins[i], 
                                           distance_bins[j], azimuth_bins[k], amount]).astype(np.float32)
                count += 1

    amounts[:, 3] = amounts[:, 3] /getVolume(ptv_roi_block)

    return elevation_bins, distance_bins, azimuth_bins, amounts


def getElevation(ptv_vox, oar_cen):
    """
    Returns the elevation between two voxels
    
    Parameters
    ----------
    ptv_vox : tuple
        Index location of PTV voxel
        
    oar_cen : tuple
        Index location of OAR centroid
        
    Returns
    -------
    elevation : int
        Elevation between voxels 
   
    """
    
    elevation = (ptv_vox[2]-oar_cen[2]) #absolute value? 
    return elevation

def getDistance(ptv_vox, oar_cen):
    """
    Returns the radial distance between two voxels
    
    Parameters
    ----------
    ptv_vox : tuple
        Index location of PTV voxel
        
    oar_cen : tuple
        Index location of OAR centroid
        
    Returns
    -------
    distance : int
        Radial distance between voxels 
   
    """
    
    distance = ((ptv_vox[0]-oar_cen[0])**2 + (ptv_vox[1]-oar_cen[1])**2 + (ptv_vox[2]-oar_cen[2])**2)**(0.5)
    return distance


def getCentroid(roi_block):
    """
    Returns the centroid (center) of an ROI_block

    Parameters
    ----------
    roi_block : 3D NdArray
        An array of dims [h x w x num_cts] where all 1s indicate
        points inside the ROI.

    Returns
    -------
    centroid : 1D NdArray
        An array of length 3, where the elements are [x, y, z]
        coordinate of the centroid respectively

    """
    
    positions = np.where(roi_block == 1)
    
    x_center = round(np.average(positions[0])).astype(np.uint8)
    y_center = round(np.average(positions[1])).astype(np.uint8)
    z_center = round(np.average(positions[2])).astype(np.uint8)

    centroid = np.array([x_center, y_center, z_center]).astype(np.float32)
    
    return centroid


def getAzimuth(ptv_vox, oar_cen):
    """
    Returns the azimuth between two voxels
    
    Parameters
    ----------
    ptv_vox : tuple
        Index location of PTV voxel
        
    oar_cen : tuple
        Index location of OAR centroid
        
    Returns
    -------
    azimuth : double
        Azimuth angle between voxels (in radians)
   
    """
    elevation = getElevation(ptv_vox, oar_cen)
    distance = getDistance(ptv_vox, oar_cen)
    
    z_over_r = elevation/distance
    azimuth = acos(z_over_r)
    return azimuth
