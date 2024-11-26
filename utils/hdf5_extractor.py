# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:58:55 2024

@author: deankos
"""

import numpy as np
from nanomol.utils.hdf5_datafile import hdf5_datafile

datafile = hdf5_datafile(mode='r')

for lv1_group_name in datafile.keys():
    for lv2_group_name in datafile[lv1_group_name].keys():
        for dataset_name in datafile[lv1_group_name][lv2_group_name].keys():
            if dataset_name == 'measured_I_DS':
                filename = '{}__{}__{}.csv'.format(lv1_group_name, lv2_group_name, dataset_name)
                data = np.array(datafile[lv1_group_name][lv2_group_name][dataset_name])
                np.savetxt(filename, np.transpose(data))
                
filename = '{}__{}__{}.csv'.format(lv1_group_name, lv2_group_name, 'calculated_V_GS')
data = np.array(datafile[lv1_group_name][lv2_group_name]['calculated_V_GS'])
np.savetxt(filename, np.transpose(data))