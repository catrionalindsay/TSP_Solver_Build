# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 11:24:28 2024

@author: Ryan
"""

import numpy as np
rnd = np.random
import math
import tsplib95 #this is a python pakage, may have to pip install 
from pathlib import Path


class Data:
    def __init__(self,n_input,width_input,seed_input):
        self.n = n_input
        self.width = width_input
        self.seed = seed_input
        self.V = range(self.n)
        self.E = [(i,j) for i in self.V for j in self.V if i <j]
        
        self.c = None
        self.loc = None
        
    def create_data(self):
        rnd.seed(self.seed)
        self.loc = {i:(rnd.random()*self.width,rnd.random()*self.width) for i in self.V}
        self.c = {(i,j): math.hypot(self.loc[i][0]-self.loc[j][0],self.loc[i][1]-self.loc[j][1]) for (i,j) in self.E}
        
        
class tsplib:
    def __init__(self, filename):
        tsp = tsplib95.load(Path.cwd() / "TSPlib_files" / filename)
        self.n = tsp.dimension
        self.V = range(0,self.n)
        self.E = [(i,j) for i in self.V for j in self.V if i <j] 
        
        self.loc = {i:(tsp.node_coords[i+1]) for i in self.V}
        self.c = {(i,j): tsp.get_weight(i+1,j+1) for (i,j) in self.E}
        
        self.width = max(self.loc.values())[0]*1.05
        self.height = max(self.loc.values(), key=lambda x: x[1])[1]*1.05

    
        #from tsp lib file 