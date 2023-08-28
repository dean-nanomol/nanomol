# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 10:24:22 2023

@author: deankos
"""

import numpy as np
import h5py
import datetime
from tkinter import Tk, filedialog

class hdf5_datafile(h5py.File):
    
    def __init__(self, mode='r'):
        """
        Parameters
        mode: str
            r: read only, file must exist
            r+: read/write, file must exist
            w: create file, truncate if exists
            w- or x: Create file, fail if exists
            a: read/write if exists, create otherwise
        """
        # hide default tk window and bring file selection window to top of window stack
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        # use today's date as file name hint
        date = str(datetime.date.today())
        if mode == 'r':
            filename = filedialog.askopenfilename(defaultextension='.hdf5')
        else:
            filename = filedialog.asksaveasfilename(initialfile=date, defaultextension='.hdf5')
        # pass file name and path to h5py library File constructor
        super().__init__(name=filename, mode=mode)
    
    
    def get_unique_group_name(self, parent_group, basename='group', max_N=1000):
        """
        Find unique child group name within given parent group

        Parameters
        parent_group : h5py group or datafile
            group within which the unique name is to be found. Pass datafile if this is the root group.
        basename : str, optional
            basename for new group name. Default is 'group'.
        max_N : int, optional
            expected maximum number of groups with same basename within parent_group. Default is 1000.
            Automatically incremented if max_N is reached without finding unique name.

        Returns
        unique_name : str
            unique group name within parent_group
        """
        counter = 0
        N_digits = int(np.log10(max_N))
        while counter < max_N:
            name_hint = '{}_{:0{}d}'.format(basename, counter, N_digits)
            if name_hint not in parent_group:
                unique_name = name_hint
                return unique_name
            counter += 1
        else:
            self.get_unique_group_name(parent_group, basename=basename, max_N=max_N*10)
    
    
    def get_unique_dataset_name(self, parent_group, basename='measurement', max_N=1000):
        """
        Find unique dataset name within given parent group

        Parameters
        parent_group : h5py group or datafile
            group within which the unique name is to be found. Pass datafile if this is the root group.
        basename : str, optional
            basename for new dataset name. Default is 'measurement'.
        max_N : int, optional
            expected maximum number of datasets with same basename within parent_group. Default is 1000.
            Automatically incremented if max_N is reached without finding unique name.

        Returns
        unique_name : str
            unique dataset name within parent_group
        """
        counter = 0
        N_digits = int(np.log10(max_N))
        while counter < max_N:
            name_hint = '{}_{:0{}d}'.format(basename, counter, N_digits)
            if name_hint not in parent_group:
                unique_name = name_hint
                return unique_name
            counter += 1
        else:
            self.get_unique_dataset_name(parent_group, basename=basename, max_N=max_N*10)


if __name__ == '__main__' :
    
    myDatafile = hdf5_datafile(mode='r')