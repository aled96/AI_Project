import sys
sys.path.insert(0, '../')
from formula import *
sys.path.insert(0, '../DPLL_Solver')
from formula_DPLL import *
from heuristics import *
from dpll import *
from plan import *
import utils

class Search():
    def __init__(self, encoder, initial_horizon):
        self.encoder = encoder
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

        #        while not self.found:
        #TODO -> Do while, increasing horizon
        for i in range(5):

            formula = self.encoder.encode(self.horizon)
            #formula in CNF
            formula = self.encoder.convert_CNF(formula)

            result = self.dimacs_and_solve(formula)

            if (result == []):
                print("No solution for horizon = "+str(self.horizon))
            else:
                print("Found a plan at horizon = "+str(self.horizon))
                print(result)
                plan = Plan(result, self.encoder)

                return

            print("\n")


            #Increase the horizon
            self.horizon += 1


    def dimacs_and_solve(self, formula_cnf):
        #Convert to DIMACS (as list)
        dimacs = list(formula_cnf)
        dimacs.insert(0,"p cnf "+str(self.encoder.f_mgr.lastId)+" "+str(len(formula_cnf)))

        #Check if SAT
        f = Formula(dimacs)
        h = PureMomsHeuristic(False)
        s = Solver(f, h)
        result = s.run()

        return result