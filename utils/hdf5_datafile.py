# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 10:24:22 2023

@author: deankos
"""

import h5py
import datetime
from tkinter import Tk, filedialog

class hdf5_datafile(h5py.File):
    
    def __init__(self, mode='r'):
        """
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
        super(hdf5_datafile, self).__init__(name=filename, mode=mode)


if __name__ == '__main__' :
    
    myDatafile = hdf5_datafile(mode='r')