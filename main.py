# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 11:30:26 2024

@author: Ryan
"""

from data_class import Data, tsplib
from model_class import TSP_model
from call_back_class import *
from helper import *
import igraph as ig
from docplex.mp.model import Model
from context import *
import cplex
import sys
import traceback
import time



output_file = "d1291.dat"
f = open(output_file, 'w')
f.write('num_threads, total_time,  warm_start_time, tspcb.num_cuts_comb,tspcb.time_cuts_comb,tspcb.num_cuts_user_cycle,tspcb.time_cuts_user_cycle,tspcb.num_cuts_lazy_cycle,tspcb.time_cuts_lazy_cycle, mdl.model.solve_details.nb_nodes_processed,mip_gap\n')
for i in range(8):
    if i in range(2):
        num_threads = 1
    
    elif i in range(2,4):
        num_threads = 2
        
    elif i in range(4,6):
        num_threads = 4
    
    elif i in range(6,8):
        num_threads = 8
     
        
    sep_frac_sols = False 
    do_warmstart = True
    
    p = tsplib('att48.tsp')
    
    mdl = TSP_model('TSP',p)
    if do_warmstart:
        w_start = time.time()
        sol_2_opt = heuristic_solve_with_2opt(p,mdl)
        w_end = time.time()
        warm_start_time = w_end-w_start
        mdl.warmstart(p, sol_2_opt)
    
    
    cpx = mdl.model.cplex
    mdl.model.context.cplex_parameters.threads = num_threads
    mdl.model.context.cplex_parameters.timelimit  = 3600
    
    tspcb = TSPCallback(num_threads, p, mdl)
    tspcb.num_cuts_comb = 0
    tspcb.num_cuts_user_cycle = 0
    tspcb.num_cuts_lazy_cycle = 0
    tspcb.cuts = []
    
    tspcb.time_cuts_comb = 0
    tspcb.time_cuts_user_cycle = 0
    tspcb.time_cuts_lazy_cycle = 0
    
    tspcb.mip_gap_root_node = 100
    
    tspcb.thread_up_counter = 0
    tspcb.thread_down_counter = 0
    
    contextmask = cplex.callbacks.Context.id.thread_up
    contextmask |= cplex.callbacks.Context.id.thread_down
    contextmask |= cplex.callbacks.Context.id.candidate
    
    #if we allow fractional solutions, do this, but we havent added in a sep_frac_sols yet
    if sep_frac_sols: 
        contextmask |= cplex.callbacks.Context.id.relaxation
     	
    cpx.set_callback(tspcb, contextmask)
    total_start = time.time()
    mdl.solve(True)
    total_end = time.time()
    total_time = total_end-total_start
    mip_gap = mdl.model.get_solve_details().mip_relative_gap
    plot_solution(p, mdl)
    
    print('total time:', total_time,'warmstart time:', warm_start_time)
    print('no comb cuts:', tspcb.num_cuts_comb, 'time comb:', tspcb.time_cuts_comb)
    print('no user cuts:', tspcb.num_cuts_user_cycle, 'time user:', tspcb.time_cuts_user_cycle)
    print('no lazy cuts:', tspcb.num_cuts_lazy_cycle, 'time lazy:', tspcb.time_cuts_lazy_cycle)
    print('mip gap', mip_gap)

    f.write('%f %f %f %f %f %f %f %f %f %f %f\n' % (num_threads, total_time,  warm_start_time, tspcb.num_cuts_comb,tspcb.time_cuts_comb,tspcb.num_cuts_user_cycle,tspcb.time_cuts_user_cycle,tspcb.num_cuts_lazy_cycle,tspcb.time_cuts_lazy_cycle, mdl.model.solve_details.nb_nodes_processed,mip_gap))

f.close()


#%%
mdl.model.solve_details.nb_nodes_processed