import sys
sys.path.insert(0, '../')
from formula import *
import utils

class Modifier():
    
    def do_encode(self):
        pass

class LinearModifier(Modifier):

    def do_encode(self, variables, bound, f_mgr):
        modifier_final = None

        #Each step one and only one action executed
        for step in range(bound):
            actions_t_i = []
            #Acquire the list of all actions negated
            for a in variables.get(step):
                actions_t_i.append(a)

            modifier = None

            count = 0
            #Put one true at a time and insert
            for i in range(len(actions_t_i)):

                modifier_at_i = None
                for j in range(len(actions_t_i)):
                    if count != j:
                        if modifier_at_i is None:
                            modifier_at_i = f_mgr.mkNot(f_mgr.getVarByName(actions_t_i[j]))
                        else:
                            modifier_at_i = utils.add_to_manager(f_mgr, modifier_at_i, f_mgr.mkNot(f_mgr.getVarByName(actions_t_i[j])), 2)
                    else:
                        if modifier_at_i is None:
                            modifier_at_i = f_mgr.getVarByName(actions_t_i[j])
                        else:
                            modifier_at_i = utils.add_to_manager(f_mgr, modifier_at_i, f_mgr.getVarByName(actions_t_i[j]), 2)
                if(modifier is None):
                    modifier = modifier_at_i
                else:
                    modifier = utils.add_to_manager(f_mgr, modifier, modifier_at_i, 1)

                count += 1
            if(modifier_final is None):
                modifier_final = modifier
            else:
                modifier_final = utils.add_to_manager(f_mgr, modifier_final, modifier, 2)

        return modifier_final



class ParallelModifier(Modifier):
    def do_encode(self, variables, mutexes, bound, f_mgr):
        pass


