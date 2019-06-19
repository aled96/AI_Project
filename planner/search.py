from planner import plan
from planner import encoder
import utils
import sys
sys.path.insert(0, '../')
from formula import *


class Search():
    def __init__(self, encoder, initial_horizon):#, formula):
        self.encoder = encoder
        #self.formula = formula
        self.horizon = initial_horizon
        self.found = False


class LinearSearch(Search):


    #Return value :
    # result -> resulting plan
    # None -> failure
    #
    def do_search(self):
        # Override initial horizon
        self.horizon = 1

        print('Start linear search')
        ## Implement linear search here
        ## and return a plan

        while not self.found:
            pass

'''
    def do_search(self):
        ## Override initial horizon
        self.horizon = 1

        print('Start linear search')
        ## Implement linear search here
        ## and return a plan

        f_mgr = FormulaMgr()

        while not self.found:
            result = self.DepthLimitedSearch(f_mgr)
            if result != None:
                self.found = True
                return result
        ## Must return a plan object
        ## when plan is found

    def DepthLimitedSearch(self, f_mgr):
        #Define inital state
        init = None
        for i in self.formula['initial']:
            if i > 0:
                v = f_mgr.mkVar(i)
            else:
                v = f_mgr.mkVar(i)
                v = f_mgr.mkNot(v)
            init = f_mgr.mkAnd(init, v)
        return self.RecursiveDLS(f_mgr, init)

    def RecursiveDLS(self,f_mgr, node):
        #if goal_test: return node
        #else if depth > limit return cutoff
        #else
        for n in self.Expand(node, f_mgr):
            result = self.RecursiveDLS(f_mgr, n)
            #if result = cutoff -> cutoff_occurred = true
            #else
            if result != None:
                return result
        #if cutoff_occurred: return cutoff else return None
        return None

    def Expand(self, node, f_mgr):
        successors = list()
        pass

'''