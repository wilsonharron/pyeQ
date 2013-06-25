'''
Created on Jun 24, 2013

@author: wharron
'''
class pyeQException(Exception): pass
class pyeQConfigurationException(pyeQException): pass
class pyeQLoginException(pyeQException): pass
class pyeQConnectionExcption(pyeQException): pass
class pyeQNotFoundException(pyeQException): pass