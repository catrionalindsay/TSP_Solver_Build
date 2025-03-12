# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 16:07:19 2024

@author: Catriona
"""
#will it push
from cplex.callbacks import *
from docplex.mp.callbacks.cb_mixin import *
import sys
import traceback
import cplex
import igraph as ig
from helper import *
from docplex.mp.cplex_engine import CplexEngine
from Worker import Worker
import time

root_node_only = True 
include_comb = True

## always set num_threads to 1 for now
class TSPCallback():
    
    def __init__(self, num_threads, data_input, model_input):
        self.num_threads = num_threads
        self.cutlhs = None
        self.cutrhs = None
        self.problem_data = data_input
        self.model_instance = model_input
        self.workers = [None] * num_threads
        
        
    def linear_ct_to_cplex(linear_ct):
        """ Converst a DOcplex linear constraint to CPLEX Python data

        :param linear_ct: a DOcplex linear constraint.
        :return: a 3-tuple containing elements representing the constraint in CPLEX-Python
            - a list of two lists, indices and coefficients , representing the linear part
            - a floating point number , the "right hand side" or rhs
            - a one-letter string (possible values are: 'L', 'E', 'G')  representing the sense of the constraint.

        Example:
            Assuming variable X has index 1, the constraint (2X <= 7) will be converted to

            ct = 2 * X <= 7
            linear_ct_cplex(ct)
            >>> [[1], [2.0]], 7.0, 'L'

        """
        cpx_lhs = CplexEngine.linear_ct_to_cplex(linear_ct=linear_ct)
        cpx_rhs = linear_ct.cplex_num_rhs()
        cpx_sense = linear_ct.sense.cplex_code
        return cpx_lhs, cpx_sense, cpx_rhs

    def separate_lazy_constraints(self, context, worker):
        
		#add all code from lazy callback
 
        # print('running lazy callback')
        # print(self.model_instance.x.values())
        
        indices = [v._index for v in self.model_instance.x.values()]
        sol = []
        for e in indices:
            sol.append(context.get_candidate_point(e))
            # print(context.get_candidate_point(e))
        # sol_x = self.make_solution_from_vars(self.model_instance.x.values())
        #print(sol_x)
        edges = []
        for e in range(len(self.problem_data.E)):
            if sol[e] > 0.000001:
                edges.append(self.problem_data.E[e])
        l_start = time.time()
        worker.separate_lazy(edges)
        l_end = time.time()
        self.time_cuts_lazy_cycle += l_end - l_start
        if worker.violated:
           
            for i in range(len(worker.cutlhs)):
                #print('adding cuts')
                #print(worker.cutlhs[i])
                context.reject_candidate(constraints=[worker.cutlhs[i], ], senses=worker.cutsense[i], rhs=[worker.cutrhs[i], ])
                self.num_cuts_lazy_cycle += 1
                
                #print('cutlhs',worker.cutlhs[i])
                self.cuts.append(worker.cutlhs[i][0])
        # print(edges)
        
        
        # print(cpx_lhs)
        # context.reject_candidate(
        # constraints=[cpx_lhs, ], senses=cpx_sense, rhs=[cpx_rhs, ])
                # ct_cpx = self.linear_ct_to_cplex(ct)
                # print(ct_cpx)
                # self.add_user_cuts(self,ct_cpx[0],ct_cpx[1],ct_cpx[2],cutmanagement=cutmanagement, local=False)
                # self.reject_candidate(self) #does this need other inputs?
                        
		# when adding the cut use reject_candidate() see callbacks.py and thge bendersatsp2.py example
	
    def separate_user_constraints(self, context, worker):
        
        #add all code from user callback
        
        # print('separate user callback')
        # print(self.model_instance.x.values())
        
        indices = [v._index for v in self.model_instance.x.values()]
        sol = []
        
        for e in indices:
            #print(e)
            sol.append(context.get_relaxation_point(e))
        #print(context.get_relaxation_point(e))
        # print(context.get_candidate_point(e))
        #sol_x = self.make_solution_from_vars(self.model_instance.x.values())
        #print(sol_x)
        
        edges = []
        weights = []    
        #print(sol)        
        for e in range(len(self.problem_data.E)):
            if sol[e] > 0.000001:
                edges.append(self.problem_data.E[e])
                weights.append(sol[e])
        if include_comb:
            c_start = time.time()
            worker.seperate_comb_inequalities(edges,weights)
            c_end = time.time()
            self.time_cuts_comb += c_end - c_start
        u_start = time.time()
        worker.separate_user_cycles(edges,weights)
        u_end = time.time()
        self.time_cuts_user_cycle += u_end - u_start
        if worker.violated:
        
            for i in range(len(worker.cutlhs)):
              
                #print(worker.cutlhs[i])
                cutmanagement = cplex.callbacks.UserCutCallback.use_cut.purge
                
            
                context.add_user_cut(cut=worker.cutlhs[i], sense=worker.cutsense[i], rhs=worker.cutrhs[i],cutmanagement=cutmanagement, local=False)
                self.num_cuts_user_cycle += 1
                
        if include_comb:
            if worker.violated_comb:
                # print('entering violated comb cut')
                for i in range(len(worker.cutlhs_comb)):
                    cutmanagement = cplex.callbacks.UserCutCallback.use_cut.purge
                    context.add_user_cut(cut=worker.cutlhs_comb[i], sense=worker.cutsense_comb[i], rhs=worker.cutrhs_comb[i],cutmanagement=cutmanagement, local=False)
                    # print('added comb cuts')        
                    self.num_cuts_comb += 1
                
	## which callback do we use
    def invoke(self, context):
        """Whenever CPLEX needs to invoke the callback it calls this
        method with exactly one argument: an instance of
        cplex.callbacks.Context.
        """
        # print('entering callback')
        # try:
       
        thread_id = context.get_int_info(
            cplex.callbacks.Context.info.thread_id)
        if context.get_id() == cplex.callbacks.Context.id.thread_up:
            # print('Thread up')
            self.thread_up_counter += 1
           
            
            self.workers[thread_id] = Worker(self.problem_data, self.model_instance)   
            
            
        elif context.get_id() == cplex.callbacks.Context.id.thread_down:
            # print('Thread down')
            
            self.workers[thread_id] = None
            
            self.thread_down_counter += 1
            
               
        elif context.get_id() == cplex.callbacks.Context.id.relaxation:
            #print('seperate user constraints')
            #print(f'node count {context.get_int_info(cplex.callbacks.CallbackInfo().node_depth)}')
            
            if root_node_only:
                if context.get_int_info(cplex.callbacks.CallbackInfo().node_depth) == 0:
                    self.separate_user_constraints(context,self.workers[thread_id])
                    self.mip_gap_root_node = abs(context.get_double_info(cplex.callbacks.CallbackInfo().best_bound) - context.get_double_info(cplex.callbacks.CallbackInfo().best_solution))/context.get_double_info(cplex.callbacks.CallbackInfo().best_solution)
                    print(self.mip_gap_root_node)
            else:
                self.separate_user_constraints(context,self.workers[thread_id])
                self.mip_gap_root_node = abs(context.get_double_info(cplex.callbacks.CallbackInfo().best_bound) - context.get_double_info(cplex.callbacks.CallbackInfo().best_solution))/context.get_double_info(cplex.callbacks.CallbackInfo().best_solution)
                print(self.mip_gap_root_node)
                
            # print('user done')
        elif context.get_id() == cplex.callbacks.Context.id.candidate:
            # print('seperate lazy constraints')
            
            self.separate_lazy_constraints(
                context,self.workers[thread_id])
            
        else:
            print("Callback called in an unexpected context {}".format(
                context.get_id()))
        # except:
        #     info = sys.exc_info()
        #     print('#### Exception in callback: ', info[0])
        #     print('####                        ', info[1])
        #     print('####                        ', info[2])
        #     traceback.print_tb(info[2], file=sys.stdout)
        #     raise
			
