

# This module provides a general class heirarchy and set of methods to implement what I'm calling system 2, and attempts to make
# no assumptions about the nature of the underlying optimization algorithms.  The only specific algorithms included in this code
# are algorithms to control and optimize the evolution of the system over time.  This would include decision functions for when to
# add new cluster sets, when to add new function interval lengths, and when to add additional layers.
#
# Usage
# 1) input data
# data is inserted into each input in the system.  Data MUST be inserted in chronological order
# If data is inserted which is older than the most recent observation, it will not be included
# in the optimization procedure
#
# 2) retrieve estimates
# inputs are queried for an estimate at a spcific time
# all optimization and clustering is done transparently at the time of a 
# data request

class sys_2_base:
# top level interface for the processing architecture
# CPDF:		algorithms for determining optimal Conditional Probability Distribution Functions
# cluster:		algorithms for clustering
# APDF:		algorithms for aggregating Probability Distribution Functions
# age_function:	algorithm to determine the kill time for a function
# t_delta_init:	the t_delta value to use for new clusters on new layers - the minimum t_delta to be used by the system
	
	layer_class = layer_base

	age_function = None
	t_delta_init = None
	
	layers = list()		# the layers defined for this system
	
	def __init__(self,age_function,t_delta_init):
		self.age_function = age_function
		self.t_delta_init = t_delta_init
		
		self.layers.append( self.layer_class(sys=self) )
		

class layer_base:
# The set of inputs and cluster spaces which define a processing layer

	input_class = input_base
	cluster_space_class = cluster_space_base

	sys = None				# the system instance this layer belongs to
	cluster_spaces = list()			# cluster spaces for this layer
	inputs = list()				# inputs for this layer
	
	def __init__(self, sys):
		self.sys = sys
		self.add_cluster_space()
		
	def add_input(self):
		i = input_class()
		self.inputs.append(i)
		return i
	
	def add_cluster_space(self, t_delta = sys.t_delta_init ):
		self.cluster_spaces.append( cluster_space_class(t_delta) )

class cluster_space_base:
# a cluster of functions
	
	t_delta = None		# the time interval length for this cluser
	
	functions = list()	# list of functions to cluster
	C = list()		# list of defined clusters	
	
	def __init__(self, t_delta=timedelta(seconds=1)):
		self.t_delta = t_delta
		
	def optimize(self):
	# determines the optimal weights for clustering the functions
	# defined in self.f and updates the clusters defined over the data
		raise StandardError, 'This function not implemented'
		
	def infer(self, CPDF, time):
	# returns a PDF at the given time based on proximity of *complete* intervals
	# to the *partial* interval (or hypothesis) given by CPDF for *each* p value
	# specified for this cluster space
		raise StandardError, 'This function not implemented'
		
class cluster_base:
# representation of a cluster in some space

	output = None		# The input at a higher level which this cluster maps to
	t_delta = None		# the time delta for this cluster
	
	def __init__(self):
		pass
		
class input_base:
# provides a representation of a source of information to the system.
# inputs take single scalar values and a timestamp.  Each component of a
# multi-dimensional source of information should have its own input instance
	
	observation_class = observation_base

	o = observation_list()			# a list of class observation instances defining the observations of this input
	f = list()				# a set of all functions defined over the observations for this input
	clusters = list()			# a set of clusters operating on this input
		
	def __init__(self):
		self.t_cache = time.now()
	
	def optimize(self,t_delta,time=None):
		raise StandardError, 'This function not implemented'
		
	def add(self, val, t=None):
	# adds an observation to the estimate
	# if no time is specified the current system time is used
	
		self.o.append( observation_class(val) )
		
	def estimate(self, time=None, hypotheses = None):
	# estimates the input's value at time under the constraints that at the time/value pairs
	# in hypothesis the input has the specified values.
		
		raise StandardError, 'This function not implemented'
			
class function_base:
# a function describing the behavior of an input over a specific observed time interval
	
	kill = None		# the kill time of the function
	
	def __init__(self,data=None,*args,**kargs):
		if data:
			self.optimize(data, *args, **kargs)
		
	def __sub__(self,a):
	# overloads the subtract function to compute distance between two functions or a function and a cluster
		raise StandardError 'This function not implemented'
		
	def optimize(self,data,CPDF,*args,**kargs):
	# optimizes data using the specified Conditional Probability Distribution Function estimator
		raise StandardError 'This function not implemented'
		
	def reg(self,t):
	# evaluates the most function at time t
		raise StandardError 'This function not implemented'
		
	def den(self,t):
	# returns a probability density over the range of the function at time t
		raise StandardError 'This function not implemented'
		
class observation_list_base(list):
# provides a container for a series of observations

	def __init__(self):
		pass
	
	def interval(self,t_start, t_delta):
	# returns a list of observations which occur between t_start and t_start + t_delta and have not yet been killed
		pass
		
	def __append__(self,*arg,**karg):
	# overloads the add operation to keep the list sorted by time
		super(self,list).__append__(*arg,**karg)
		self.sort(sort_time)
		
class observation_base(list):
# provides a representation of a single piece of data at a set time

	def __init__(self, val, t=None):
		super(self,list).__init__()
		
		self[0] = t and t or time.now()
		self[1] = val
	
	def __getattr__(self,value):
		if value == 'val':
			return self[1]
		elif value == 't':
			return self[0]
