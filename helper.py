# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 11:44:25 2024

@author: Ryan
"""
import matplotlib.pyplot as plt

import igraph as ig

from docplex.mp.model import Model

def get_cutset(E,S):
    cut_set = [(i,j) for (i,j) in E if (i in S and j not in S) or (j in S and i not in S)]
    return cut_set

def find_path_from_edges(edges):

    graph = {}
    for v1, v2 in edges:
        if v1 not in graph:
            graph[v1] = []
        if v2 not in graph:
            graph[v2] = []
        graph[v1].append(v2)
        graph[v2].append(v1)  
        
    visited = set()
    paths = []

    # Use a queue for a breadth-first-like approach
    for start_vertex in graph.keys():
        if start_vertex not in visited:
            path = []
            current_vertex = start_vertex
            
            # Iteratively build the path
            while current_vertex not in visited:
                visited.add(current_vertex)
                path.append(current_vertex)
                
                # Move to the next unvisited neighbor
                for neighbor in graph[current_vertex]:
                    if neighbor not in visited:
                        current_vertex = neighbor
                        break
                else:
                    # No unvisited neighbors, break the loop
                    break
            
            # Only store the path if it has more than one vertex
            if len(path) > 1:
                paths.append(path)

    return paths

def find_edge_path_from_node_path(node_path):
    new_path = []
    for i in range(len(node_path)-1):
            A = node_path[i]
            B = node_path[i+1]
            new_path.append((min(A,B),max(A,B)))
    
    #add final edge
    new_path.append((min(node_path[0], node_path[-1]), max(node_path[0],node_path[-1])))
    return new_path 


def find_connected_components(edges):
    components=[]
    for v1, v2 in edges:
        for component in components:
            if v1 in component:
                for i, other_component in enumerate(components):
                    if v2 in other_component and other_component != component: # v1, and v2 are already in different components: merge
                        component.extend(other_component)
                        components[i:i+1] = []
                        
                else: # b wasn't found in any other component
                    if v2 not in component:
                        component.append(v2)
                
            if v2 in component: # v1 wasn't in in the component 
                component.append(v1)
                
        else: # neither v1 nor v2 were found
            components.append([v1, v2])
    return components

def  cycle_close_check(path, edge):
    '''
    does this edge close a cycle when added to this path?
    '''
    v1,v2 = edge
    
    # Step 1: Find connected components in the current path
    connected_components = find_connected_components(path)

    # Step 2: Check if both v1 and v2 are in the same component
    for component in connected_components:
        if v1 in component and v2 in component:
        # v1 and v2 are already connected, so adding this edge would close a cycle
            print('dont add this edge', component, (v1,v2))
            return True
    #print(connected_components)
    return False

def plot_solution(data, model, edges_to_plot=None):
    plt.figure()
    
    # Plot vertices
    for i in data.V:
        plt.scatter(data.loc[i][0], data.loc[i][1], c='black')
        plt.annotate(i, (data.loc[i][0] + 2, data.loc[i][1]))

    # Plot edges based on model solution
    if edges_to_plot is None:
        for (i, j) in data.E:
            if model.x[i, j].solution_value > 0.9:
                plt.plot([data.loc[i][0], data.loc[j][0]], [data.loc[i][1], data.loc[j][1]], c='red')

    #Plot specified edges - I added in to check the 2opt was working, can remove
    if edges_to_plot is not None:
        for (i, j) in edges_to_plot:
            plt.plot([data.loc[i][0], data.loc[j][0]], [data.loc[i][1], data.loc[j][1]], c='blue', linewidth=2)

    plt.axis([0, data.width, 0, data.height])
    plt.grid()
    fig = plt.gcf()
    fig.set_size_inches(8, 8)
    plt.show()


# Helper function to calculate the total distance of a given path
def calculate_total_cost(path, data):
    total_cost = 0
    for (i, j) in path:
        total_cost += data.c[(min(i, j), max(i, j))]
    return total_cost


def heuristic_nearest_neighbour(data):
    """
    This is a nearest neighbour solver. 
    Note that this is a sub optimal solution but can be used as an upper bound.
    """
    #create list of vertices
    available_vertices = list(data.V)

    #choose initial starting point 
    min_edge = min(data.c, key=data.c.get)  # (i, j) with the smallest distance
    # print('e',min_edge,'e')
    start_v, second_v = min_edge  # Start with the two vertices of the min edge
    available_vertices.remove(start_v)
    
    #create path with starting point included 
    path = [(start_v, second_v)]
    
    #create variable for the current vertex
    current_v = second_v
    
    #loop over the number of vertices minus the starting vertex
    for j in data.V[:-2]:
        
        #start near at infinity, all edges have a lower cost 
        near = float('inf')
        
        #remove current vertex
        available_vertices.remove(current_v)
        
        #loop over remaining vertices
        for i in available_vertices:
            
            #this is looking in tuples of form (current vertex, i)
            if i> current_v:
                
                #if the cost is less than near, overwrite near
                if data.c[(current_v,i)] < near:
                    
                    near = data.c[(current_v,i)]
                    
                    #choose this as the next vertex
                    next_vertex = i  
            
            #this is looking in tuples of form (i,current vertex)
            elif current_v>i:
                
                #if the cost is less than near, overwrite near
                if data.c[(i,current_v)] < near:
                    
                    near = data.c[(i,current_v)]
                    
                    #choose this as the next vertex
                    next_vertex = i 
        
        #add final vertex
        if current_v < next_vertex:
            path.append((current_v,next_vertex))
        else:
            path.append((next_vertex,current_v))
        #relabel new current vertex
        current_v = next_vertex
        
    
    if current_v < start_v:
        path.append((current_v,start_v))
    else:
        path.append((start_v,current_v))
        
    return path, calculate_total_cost(path,data)


def heuristic_solve_with_2opt(data, model):
    
    def two_opt_cost(A, B, C, D):
        # Return updated cost
        return data.c[min(A, C), max(A, C)] + data.c[min(B, D), max(B, D)] - data.c[min(A, B), max(A, B)] - data.c[min(C, D), max(C, D)]
    
    # Find initial heuristic solution
    path = heuristic_nearest_neighbour(data)[0]
    
    #convert to path of nodes
    node_path = find_path_from_edges(path)[0]
    
    # Calculate initial cost
    total_cost = calculate_total_cost(path, data)

    print('heuristic solution', path ,total_cost)
       
    improved = True
    
    #this ensures that if an improvement swap is made, it will check again to see if any further improvements can be made 
    while improved:

        improved = False
        
        #-3 leaves space for 2 nodes to be reversed at the end 
        for i in range(0, len(node_path)-3):
            
            #leaves space for 2 nodes to be reversed at the start and end
            for j in range(i + 2, len(node_path)-1):
                
                #calculate change in cost for the proposed node swap
                cost_change = two_opt_cost(node_path[i - 1], node_path[i], node_path[j -1], node_path[j])
                
                # If the cost change is negative, we found an improvement
                if cost_change < 0:
                    
                    #Reverse the segment between i and k
                    node_path[i:j] = reversed(node_path[i:j])
    
                    # Update the total cost
                    total_cost += cost_change
                    
                    #set improved to true so it can check again for further improvements 
                    improved = True 
                  
    #change back into edge path 
    edge_path = find_edge_path_from_node_path(node_path)
            
    return edge_path, total_cost

 
def heuristic_greedy(sorted_edges,data):

    #create dictionary to store the vertex degrees 
    vertex_degree = {v: 0 for v in data.V}
    
    path = []
    
    #loop over the sorted edges
    for (v1, v2) in sorted_edges: #difference in data structure here
        
        #if the final edge in the cycle
        if len(path)+1 == len(data.V):
            
            #close the final edge
            if vertex_degree[v1] ==1 and vertex_degree[v2]==1:
                # print('the last appends',(v1,v2))
                path.append((v1, v2))
                
                # Increase the degree of the vertices
                vertex_degree[v1] += 1
                vertex_degree[v2] += 1
                
                return path, calculate_total_cost(path, data)

    
        # Check if adding this edge would violate the valency
        elif vertex_degree[v1] < 2 and vertex_degree[v2] < 2:
            # Check if adding this edge would create a cycle
            # print(len(path), len(data.V))
            if cycle_close_check(path, (v1,v2)) ==True: #write a cycle check function 
                # print('closes cycle',(v1,v2))
                continue
                
            else:
                # print('appends',(v1,v2))
                path.append((v1, v2))

                # Increase the degree of the vertices
                vertex_degree[v1] += 1
                vertex_degree[v2] += 1
                
    # print('partial solution found')
    return path, calculate_total_cost(path, data)
      
def cycle_finder(data, model):
    """
    Takes data and model inputs and makes it igraph compatible,
    allowing us to find the components.

    """
    # Create an igraph Graph
    g = ig.Graph()
    g.add_vertices(data.n)
    
    
    model.solve(True)
    
    solution_edges = [(i, j) for (i, j) in data.E if model.x_sol[(i, j)] > 0]
    g.es['solution'] = [model.x_sol[e] for e in solution_edges]
    cost = [data.c[e] for e in solution_edges]
    
    g.add_edges(solution_edges)
    
    g.es['cost'] = cost
    
    cycles = g.connected_components(mode='weak')
    
    return cycles 
                 
def cycle_finder_from_path(data,path):
    g = ig.Graph()
    g.add_vertices(data.n)
    
    g.add_edges(path)
    
    cost = [data.c[e] for e in path]
    g.es['cost'] = cost
    
    cycles = g.connected_components(mode='weak')
    
    return cycles



    