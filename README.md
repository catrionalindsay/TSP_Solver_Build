# TSP_Solver_Build

These files are a solver for the travelling salesman problem using IBM'S ILOG CPLEX. <br />
<br />
To run the solver, download all files. The solver can be run through the main.py, with the following variations:<br />
<br />
num_threads: Number of threads used by the solver. <br />
do_warmstart: Set to True/ False to turn the warmstart on and off.<br />
sep_frac_sols: Set to True/False to use user cuts or not.<br />
p: The problem instance. This can be either a random set of points or a TSPLIB file. More information is contained within data_class.  <br />
output_file: Name of a file the results are written to. <br />
<br />
The following adjustments can be made in the context.py file:<br />
<br />
root_node_only: Set to True/False to use user cuts only at the root node or everywhere. <br />
include_comb: Set to True/Flase to include comb inequalities wherever user cuts are added. <br />
