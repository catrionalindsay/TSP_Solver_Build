# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 11:18:41 2025

@author: Catriona
"""
import igraph as ig 
from helper import *
from docplex.mp.cplex_engine import CplexEngine

class Worker:
    def __init__(self, data_input, model_input):
        
        self.problem_data = data_input
        self.model_instance = model_input
        self.violated = False
        self.violated_comb = False
        
    def separate_lazy(self, edges):
        """
        Adds Lazy cuts to CPLEX model

        """
    
        self.cutlhs = []
        self.cutrhs = []
        self.cutsense = []
        self.violated = False
        g = ig.Graph()
        g.add_vertices(self.problem_data.n)
        g.add_edges(edges)

        cycles = g.connected_components(mode='weak')

        if len(cycles) > 1:
            self.violated = True
            for cycle in cycles:
    
                ct = self.model_instance.model.sum(self.model_instance.x[e]

                                        for e in get_cutset(self.problem_data.E, cycle)

                                            ) >= 2
                #print(ct)
                self.cutlhs.append(CplexEngine.linear_ct_to_cplex(linear_ct=ct))
                self.cutrhs.append(ct.cplex_num_rhs())
                self.cutsense.append(ct.sense.cplex_code)
       

    def seperate_comb_inequalities(self, edges, weights):
        """ 
        Adds comb inequalities to CPLEX model
        """
        print('adding comb')
        self.cutlhs_comb = []
        self.cutrhs_comb = []
        self.cutsense_comb = []
        self.violated_comb = False
        
        frac_edges = []
        frac_weights = []
        int_edges = []
        
        for i in range(len(weights)):
            #add to list of fractional solutions
            if weights[i] >1e-5 and weights[i] < 1-1e-5:
                frac_edges.append(edges[i])
                frac_weights.append(weights[i])
            #add to list of teeth potentials
            elif weights[i] >1-1e-5:
                int_edges.append(edges[i])
        
        gfrac = ig.Graph()
        gfrac.add_vertices(self.problem_data.n)
        gfrac.add_edges(frac_edges)
        components = gfrac.connected_components(mode='weak')

        
        used_vertices = []
        for comp in components:

            if len(comp) %2 ==0 or len(comp) ==1:
                continue
            elif len(comp) %2 ==1 and len(comp)>2: #this is the handle of a comb 
                teeth_edges = []
                
                for i in comp: #i is handle vertex
                    
                    for (j,k) in int_edges:
                        if (k == i or j==i) and k not in used_vertices and j not in used_vertices:
                            teeth_edges.append((j,k))
                            used_vertices.append(j)
                            used_vertices.append(k)

                if len(teeth_edges) == len(comp):
                    
                    self.violated_comb = True 
                    rhs = len(comp) + (len(teeth_edges)-1)/2 #from comb inequality reading
                    handle_edges = []
                    for h in range(len(comp)-1):
                        for g in range(h+1,len(comp)):
                            x = comp[h]
                            y = comp[g]
                            handle_edges.append((min(x,y),max(x,y)))
                            
                    lhs = self.model_instance.model.sum(self.model_instance.x[w] for w in handle_edges) + self.model_instance.model.sum(self.model_instance.x[z] for z in teeth_edges)
                    comb_ineq = rhs >= lhs
                    self.cutlhs_comb.append(CplexEngine.linear_ct_to_cplex(linear_ct=comb_ineq))
                    self.cutrhs_comb.append(comb_ineq.cplex_num_rhs())
                    self.cutsense_comb.append(comb_ineq.sense.cplex_code)        
                        
             
    def separate_user_cycles(self,edges, weights):
        """ 
        Adds user cuts to CPLEX model
        """
            
        self.cutlhs = []
        self.cutrhs = []
        self.cutsense = []
        self.violated = False
        #print(edges)
        g = ig.Graph()
        g.add_vertices(self.problem_data.n)
        g.add_edges(edges)
        cycles = g.connected_components(mode='weak')

        if len(cycles) > 1:
            self.violated = True
            for cycle in cycles:

                ct = self.model_instance.model.sum(self.model_instance.x[e]

                                        for e in get_cutset(self.problem_data.E, cycle)

                                            ) >= 2
                
                self.cutlhs.append(CplexEngine.linear_ct_to_cplex(linear_ct=ct))
                self.cutrhs.append(ct.cplex_num_rhs())
                self.cutsense.append(ct.sense.cplex_code)
       
        else:
            
            g.es['weight'] = weights
            cut = g.mincut()

            if cut.value < 2: #the total weight of the edges that form the cutset
                self.violated = True
                for cycle in cut.partition:
                    ct = self.model_instance.model.sum(self.model_instance.x[e]

                                            for e in get_cutset(self.problem_data.E, cycle)

                                                ) >= 2
                    
                    self.cutlhs.append(CplexEngine.linear_ct_to_cplex(linear_ct=ct))
                    self.cutrhs.append(ct.cplex_num_rhs())
                    self.cutsense.append(ct.sense.cplex_code)
