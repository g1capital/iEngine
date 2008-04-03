#! /usr/bin/env python

import sys, getopt, math, datetime, os
from math import sqrt

from numpy import *
from pylab import plot,bar,show,legend,title,xlabel,ylabel,axis

from cvxopt.base import *
from cvxopt.blas import dot 
from cvxopt.solvers import qp

from cvxopt import solvers
#solvers.options['show_progress'] = False

from santa_fe import getData

_Functions = ['run']
	
def sign(x,y):
	if isinstance(x, (int, long, float)):
		return int( x > 0 )
	else:
		return int( sum(x>y) == len(x) )
		return int( x.min() > 0)
class estimate:
	def __init__(self,x,y,kernel):
		# set variables
		if len(x) != len(y):
			raise StandardError, 'input/output values have different cardinality'
		self.l = len(x)
		self.x = x
		self.y = y
		self.kernel = kernel
		self.beta = None

	def xy(self,i,j):
	################################################################################
	#
	#	F_\ell(y,x) = frac{1}{\ell} \sum_{i=1}^{\ell} \theta(y-y_i) \theta(x-x_i)
	#
	# where y=i, x=j, l=self.l
	# and i,j are both vectors of x and y (not indices of training data)
	#
	################################################################################
	
		signmatrix = array( [ sign(i,self.x[k])*sign(j,self.y[k]) for k in range(self.l) ] )
		return sum(signmatrix)/self.l
	
	def equality_check(self):
		c_matrix = matrix(0.0,(self.l,self.l))
		for i in range(self.l):
			for j in range(self.l):
				c_matrix[i,j] = self.beta[j]*self.kernel.xx[i,j]/self.l
		return sum(c_matrix)

	def inequality_check(self):
		c_matrix = matrix(0.0,(self.l,1))
		for p in range(self.l):
			p_matrix = matrix(0.0,(self.l,self.l))
			for i in range(self.l):
				for j in range(self.l):
					p_matrix[i,j] = self.beta[i]*(self.kernel.xx[j,i]*sign(self.x[p],self.x[j])*
					self.kernel.int(p,i)-self.xy(self.x[p],self.y[p]))/self.l
			c_matrix[p,0] = sum(p_matrix)
		return c_matrix

class kernel:
	def __init__(self,data,gamma,sigma_q):
		# set variables
		self.l = len(data)-1
		self.n = len(data[0])
		self.gamma = gamma
		self.sigma = sigma_q/sqrt(self.l)
		self.x = data[:-1]
		self.y = data[1:]
		self.xx = matrix(0.0,(self.l,self.l))
		self.yy = matrix(0.0,(self.l,self.l))
		
		# calculate xx matrix
		for i in range(self.l):
			print 'x_ (%s, n) of %s calculated' % (i,self.l)
			for j in range(self.l):
				if j>=i:
					val = self._calc(self.x[i],self.x[j])
					self.xx[i,j] = val
					self.xx[j,i] = val
		f=open('xx.matrix','w')
		self.xx.tofile(f)
		f.close()
		print 'xx saved to file'
		
		# calculate yy matrix
		#FIXME: Work integration into here?
		for i in range(self.l):
			print 'y_ (%s, n) of %s calculated' % (i,self.l)
			for j in range(self.l):
				if j>=i:
					val = self._calc(self.y[i],self.y[j])
					self.yy[i,j] = val
					self.yy[j,i] = val
		f=open('yy.matrix','w')
		self.yy.tofile(f)
		f.close()
		print 'yy saved to file'

		# Normalize
		self.xx /= sum(self.xx)
		self.yy /= sum(self.yy)

	def int(self,i,j):
		# \int_{-\infty}^{y_i} K_\gamma{y_i,y_j}dy_i
		# When y_i is a vector of length 'n', the integral is a coordinate integral in the form
		# \int_{-\infty}^{y_p^1} ... \int_{-\infty}^{y_p^n} K_\gamma(y',y_i) dy_p^1 ... dy_p^n
		# note that self.y is a vector array, while self.yy is a matrix of K values
		# 
		# After going over the math, the integral of the function should be calculated as follows
		# take the sum of K for all values of y which have at least one dimension less than y_p
		# times the inverse of lxn where l is the total number of y and n is the dimensionality of y
		
		# select the row (*,j) of self.yy 
		yi = self.yy[self.l*j:self.l*(j+1)]
		for n in range(self.l):
			# scale K according to how many dimensions are less than y_p 
			# ( note that this also zeroes out y which are larger than y_p)
			yi[n,0] = yi[n,0]*(sum(self.y[n]<self.y[i]))
			
		# return the sum of the remaining values of K divided by lxn where l is the number of y and n is the dimensionality
		return sum(yi)/(self.l*self.n)

	def _calc(self,a,b):
	 	return math.exp(-linalg.norm((a-b)/self.gamma))

def run():
	# Retrieve dataset
	data = getData('B1.dat')[:100]
	
	# Construct Variables
	K = kernel(data,gamma=1,sigma_q=.5)
	F = estimate(data[:-1],data[1:],K)
	
	# Objective Function
	print 'constructing objective function...'
	P = matrix(0.0,(K.l,K.l))
	for m in range(K.l):
		for n in range(K.l):
			if (n+1)==K.l:
				n = K.l-n-1
			P[m,n] = K.xx[n,m]*K.yy[n,m]
	q = matrix(0.0,(K.l,1))

	# Equality Constraint
	print 'constructing equality constraints...'
	A = matrix(0.0, (1,K.l))
	for n in range(K.l):
		A[n] = sum(matrix( [ K.xx[i,n] for i in range(K.l) ] ) ) / K.l
	#A = matrix(0.0, (N,N))
	#for m in range(N):
	#	for n in range(N):
	#		A[m,n] = K.xx[m,n] / N
	#b = matrix(1.0,(N,1))
	b = matrix(1.0)
	
	# Inequality Constraint
	print 'construction inequality constraints...'
	G = matrix(0.0, (K.l,K.l))
	for m in range(K.l):		
		print "Inequality (%s,n) of %s calculated" % (m,K.l)
		for n in range(K.l):
			# CHECK THIS MATH - it's probably wrong, but you get the point
			K_int = K.int(n,m)
			def f(a,x):
				Kxx = K.xx[m::K.l]
				xn = resize(array(K.x[n]),(K.l,1))
				xx = array(K.x)
				return xx*K_int*(xn>xx)
			a=fromfunction(f,(1,K.l))
			if (m+1)==K.l:
				m = K.l-m-1
			G[n,m] = sum(a)/K.l - F.xy(data[n],data[n])
	h = matrix(K.sigma, (K.l,1))

	# Optimize
	print 'starting optimization...'
	print 'P.size = %s' % repr(P.size)
	print 'q.size = %s' % repr(q.size)
	print 'G.size = %s' % repr(G.size)
	print 'h.size = %s' % repr(h.size)
	print 'A.size = %s' % repr(A.size)
	print 'b.size = %s' % repr(b.size)
	optimized = qp(P, q,G= G, h=h, A=A, b=b)
	F.beta = optimized['x']
	f=open('beta.matrix','w')
	F.beta.tofile(f)
	f.close()
	print 'beta saved to file'

	# Display Results
	print 'optimized'
	print 'data points: %s' % K.l

	
def help():
	print __doc__
	return 0
	
def process(arg='run'):
	if arg in _Functions:
		globals()[arg]()
	class Usage(Exception):    def __init__(self, msg):        self.msg = msgdef main(argv=None):	if argv is None:		argv = sys.argv	try:		try:			opts, args = getopt.getopt(sys.argv[1:], "hl:d:", ["help","list=","database="])		except getopt.error, msg:			raise Usage(msg)
				# process options		for o, a in opts:			if o in ("-h", "--help"):
				for f in _Functions:
					if f in args:
						apply(f,(opts,args))
						return 0				help()
				# process arguments		for arg in args:			process(arg) # process() is defined elsewhere
	except Usage, err:		print >>sys.stderr, err.msg		print >>sys.stderr, "for help use --help"		return 2if __name__ == "__main__":	sys.exit(main())
