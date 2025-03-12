# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 11:35:58 2024

@author: Ryan
"""
from docplex.mp.model import Model
from helper import *

class TSP_model:
    
    def __init__(self,model_name,data):
        self.model = Model("TSP")
        self.x = self.model.binary_var_dict(data.E, name = 'x')
        self.obj = self.model.sum(data.c[i,j]*self.x[i,j] for (i,j) in data.E)
        self.model.minimize(self.obj)
        
        self.degree_cts = self.model.add_constraints(self.model.sum(self.x[e] for e in get_cutset(data.E,[j])) == 2 for j in data.V)
    
    def solve(self,output_log):
        self.solution = self.model.solve(log_output = output_log)
        self.x_sol = self.solution.get_value_dict(self.x)
        
    
    def warmstart(self, data, heuristic): #add heuristic into input
        """
        Takes the data, runs the heuristic solution and uses the heuristic to 
        make a dictionary which is then used as a starting point for solving the model
        """ 
        #find heuristic path and cost 
        path, cost = heuristic[0], heuristic[1]
        
        #create new solution
        warmstart = self.model.new_solution()
        
        #loop over the edges
        for e in data.E: 
        
            #if e in heuristic solution assign value 1 in dictionary, else 0
            if e in path:

                #add the dictionary to the warmstart
                warmstart.add_var_value(f'x_{e[0]}_{e[1]}', 1)
                
            else:
                #add the dictionary to the warmstart
                warmstart.add_var_value(f'x_{e[0]}_{e[1]}', 0)
        
        #add the warmstart to the model
        self.model.add_mip_start(warmstart)
        
        
        
    