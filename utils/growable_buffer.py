# -*- coding: utf-8 -*-
"""
Growable numpy arrays for measurement data.

A python list handed to pyqtgraph is converted to a numpy array with np.array()
on every update, so the whole history is copied again on each plot refresh.
These arrays grow geometrically instead: appending a point is amortised
constant time, and the slices handed out are views, so nothing is copied.
"""

import numpy as np


class growable_buffer:
    """Arrays of doubles that grow on demand, indexed by name."""

    def __init__(self, names, capacity=1024):
        self._arrays = {name: np.empty(capacity) for name in names}
        self._lengths = {name: 0 for name in names}

    def append(self, name, value):
        length = self._lengths[name]
        if length == self._arrays[name].size:
            grown = np.empty(length * 2)
            grown[:length] = self._arrays[name]
            self._arrays[name] = grown
        self._arrays[name][length] = value
        self._lengths[name] = length + 1

    def __getitem__(self, name):
        return self._arrays[name][:self._lengths[name]]

    def items(self):
        return [(name, self[name]) for name in self._arrays]
