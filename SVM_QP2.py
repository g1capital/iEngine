#! /usr/bin/env python

# This is based on "multivariate density estimation - a support vector approach"

# STATUS:
# The algorithm appears to be working correctly, however it is very sensitive to the
# input parameters, and the computational cost increases exponentially with the
# number of observations - I get unacceptable performance with under 1000 points.
#
# One thing to look into is how cvxmod is formulating the problem, it says it is using
# the 'nonlinear' solver, which may indicate it's doing some unnecessarily complicated
# stuff.  
#
# This is only formulated for the single-variate case - to move up in dimension I'll need
# to change how the kernel is formulated to allow correct transposes and to add a product
# operator.  This will also apply to the CMF calculation

import sys, getopt, math, datetime, os, cmath
from random import gauss

import numpy
import scipy
import scipy.special
import scipy.stats
import cvxopt
import cvxmod
from cvxopt import *

from numpy import *

import matplotlib.pyplot as plt

_Functions = ['run']
	
class svm:
	def __init__(self,data=list(),gamma =1.2, C=1e1):
		self.data = data
		self.Fl = None
		self.SV = None
		self.beta = None

		self.gamma = gamma
		self.C = C
		
		self._compute()
	
	def _K(self,X,Y,gamma):
		# Gaussian kernel w/ width gamma
		# NOTE: this is only applicable to 1d data points
		return ( 1/( gamma * sqrt( 2*pi ) ) ) * exp( -( ( X - Y )**2 ) / (2 * ( gamma**2 ) ) )
		
	def Pr(self,x):
		return numpy.dot(self.beta, self._K(self.SV,x,self.gamma) )[0][0]
	
	def __iadd__(self, points):
		# overloaded '+=', used for adding a vector list to the module's data
		# 
		# @param points		A LIST of observation vectors (not a single ovservation)
		self.data += points
	
	def _compute(self):
		C = self.C
		gamma = self.gamma
		(N,d) = self.data.shape
		X = self.data

		Xcmf = ( (X.reshape(N,1,d) > transpose(X.reshape(N,1,d),[1,0,2])).prod(2).sum(1,dtype=float) / N ).reshape([N,1])
		sigma = .75 / sqrt(N)
		
		K = self._K( X.reshape(N,1,d), transpose(X.reshape(N,1,d), [1,0,2]), gamma ).reshape([N,N])
		#NOTE: this integral depends on K being the gaussian kernel
		Kint =  ( (1.0/gamma)*scipy.special.ndtr( (X-X.T)/gamma ) )
		
		alpha = cvxmod.optvar( 'alpha',N,1)
		alpha.pos = True
		xi = cvxmod.optvar( 'xi', N,1 )
		xi.pos = True
		pXcmf = cvxmod.param( 'Xcmf', N, 1 )
		pXcmf.pos = True
		pXcmf.value = cvxopt.matrix( Xcmf, (N,1) )
		pKint = cvxmod.param( 'Kint', N, N )
		pKint.value = cvxopt.matrix( Kint, (N,N) )
		
		objective = cvxmod.minimize( cvxmod.sum( cvxmod.atoms.power(alpha, 2 ) ) + ( C * cvxmod.sum( xi ) ) )
		eq1 = cvxmod.abs( ( pKint * alpha ) - pXcmf ) <= sigma + xi
		eq2 = cvxmod.sum( alpha ) == 1.0
		
		# Solve!
		p = cvxmod.problem( objective = objective, constr = [eq1, eq2] )
		p.solve()
		
		beta = ma.masked_less( alpha.value, 1e-7 )
		mask = ma.getmask( beta )
		data = ma.array(X,mask=mask)
		
		self.beta = beta.compressed().reshape([ 1, len(beta.compressed()) ])
		self.SV = data.compressed().reshape([len(beta.compressed()),1])
		print "%s SV's found" % len(self.SV)
		
def run():
	mod = svm( array([[gauss(0,1)] for i in range(400) ] + [[gauss(8,1)] for i in range(400) ]).reshape([800,1]) )
	
	X = arange(-5.,11.,.05)
	Y_cmp = [ mod.Pr(x) for x in X ]
	
	n, bins, patches = plt.hist(mod.data, 10, normed=1, facecolor='green', alpha=0.5, label='empirical distribution')
	#bincenters = 0.5*(bins[1:]+bins[:-1])
	#plt.plot(bincenters, n, 'r', linewidth=1)
	
	plt.plot( mod.SV, [ mod.Pr(x ) for x in  mod.SV ], 'o', label="SV's" )
	#plt.plot(mod.data,mod.Fl, 'o',label='empirical CDF')
	plt.plot(X,Y_cmp, 'r--', label='computed PDF')
	plt.legend()
	plt.show()
	
	
def help():
	print __doc__
	return 0
	
def process(arg='run'):
	if arg in _Functions:
		globals()[arg]()
	
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(sys.argv[1:], "hl:d:", ["help","list=","database="])
		except getopt.error, msg:
			raise Usage(msg)
		
		# process options
		for o, a in opts:
			if o in ("-h", "--help"):
				for f in _Functions:
					if f in args:
						apply(f,(opts,args))
						return 0
				help()
		
		# process arguments
		for arg in args:
			process(arg) # process() is defined elsewhere
			
	except Usage, err:
		print >>sys.stderr, err.msg
		print >>sys.stderr, "for help use --help"
		return 2

if __name__ == "__main__":
	sys.exit(main())
