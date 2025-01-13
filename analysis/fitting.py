# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 15:44:49 2024

@author: deankos

Collection of funcions useful for data fitting.
"""

import numpy as np
import scipy
import math

def find_best_linear_fit(X, Y, fit_width, fit_section_start, fit_section_stop):
    """
    Returns the best (highest R) linear fit of width fit_width available in the data section between
    fit_section_start and fit_section_stop.

    Parameters
    ----------
    X : numpy array
        X data.
    Y : numpy array
        Y data, same size as X.
    fit_width : int
        number of consecutive data points to be fitted, i.e. width of linear fit section.
    fit_section_start : int
        index of first point of data range where to look for best fit.
    fit_section_stop : TYPE
        index of last point of data range where to look for best fit.

    Returns
    -------
    best_fit_centre_index : int
        index of data point where best fit was found.
    best_fit_centre_X : float
        X value at best_fit_centre_index.
    fitted_X : numpy array
        X values over which the best fit was calculated.
    slope : float
        slope of best fit.
    intercept : type
        intercept of best fit.
    R2 : float
        R squared of best fit.
    """
    
    fit_centre_points = range(fit_section_start + fit_width//2, fit_section_stop - fit_width//2 +1)   
    fit_indices = []
    fit_R2 = []
    fit_slopes = []
    fit_intercepts = []
    for i in fit_centre_points:
        fit_indices.append(i)
        X_slice = X[(i-fit_width//2):(i+fit_width//2)]
        Y_slice = Y[(i-fit_width//2):(i+fit_width//2)]
        fit = scipy.stats.linregress(X_slice, Y_slice)
        fit_slopes.append(fit[0])
        fit_intercepts.append(fit[1])
        fit_R2.append(fit[2]**2)
    
    max_R2_index = np.argmax(fit_R2)
    best_fit_centre_index = fit_centre_points[max_R2_index]
    best_fit_centre_X = X[best_fit_centre_index]
    fitted_X = X[best_fit_centre_index-fit_width//2 : best_fit_centre_index+fit_width//2 +1]
    slope = fit_slopes[max_R2_index]
    intercept = fit_intercepts[max_R2_index]
    R2 = fit_R2[max_R2_index]
    
    return (best_fit_centre_index, best_fit_centre_X, fitted_X, slope, intercept, R2)


def fit_noise(fit_function, X_data, Y_data, **kwargs):
    """
    Returns the noise function fitted to X_data, Y_data. Uses scipy.optimize.curve_fit for fitting.

    Parameters
    ----------
    fit_function : str
        function used for fitting the noise data, one of the following:
        'constant': fits a constant, f(x) = a. Use e.g. for flat baseline noise.
        'sinudoid': fits f(x) = a*sin(omega*x+b) +c. Use e.g. for line frequency noise with time as x.
    X_data : numpy array
        X data used for fitting.
    Y_data : numpy array
        Y data usef for fitting, must have same size as X.
    **kwargs
        any keyworded arguments are passed to scipy.optimize.curve_fit, e.g. initial guess, bounds

    Returns
    -------
    fitted_func : function
        function that returns fitted noise given an x value or array as argument
    """
    
    if fit_function == 'constant':
        def constant_func(x, a):
            return np.ones(x.size) * a
        params, params_covariance = scipy.optimize.curve_fit(constant_func, X_data, Y_data, **kwargs)
        a = params
        def fitted_func(x):
            return np.ones(x.size) * a
        
    elif fit_function == 'sinusoid':
        def sinusoid_func(x, a, b, c, freq):
            omega = 2*math.pi * freq
            return a * np.sin(omega*x +b) + c
        params, params_covariance = scipy.optimize.curve_fit(sinusoid_func, X_data, Y_data, **kwargs)
        a, b, c, freq = params
        def fitted_func(x):
            omega = 2*math.pi * freq
            return a * np.sin(omega*x +b) + c
        
    return fitted_func