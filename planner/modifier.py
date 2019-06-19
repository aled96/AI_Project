import sys
sys.path.insert(0, '../')
from formula import *

class Modifier():
    
    def do_encode(self):
        pass

class LinearModifier(Modifier):

    def do_encode(self, variables, bound, f_mgr):
        c = []
        modifier = None

        ### TODO -> KEEP attention at intial value of formula and c (since I do c = (c --) )
        #Each step one and only one action executed
        for step in range(bound):
            actions_t_i = []
            #Acquire the list of all actions negated
            for a in variables.get(step):
                actions_t_i.append(a)

            count = 0
            #Put one true at a time and insert
            for i in range(len(actions_t_i)):

                for j in range(len(actions_t_i)):
                    if count != j:
                        if modifier is None:
                            modifier = f_mgr.mkNot(f_mgr.getVarByName(actions_t_i[j]))
                        else:
                            modifier = f_mgr.mkAnd(modifier, f_mgr.mkNot(f_mgr.getVarByName(actions_t_i[j])))
                    else:
                        if modifier is None:
                            modifier = f_mgr.getVarByName(actions_t_i[j])
                        else:
                            modifier = f_mgr.mkAnd(modifier, f_mgr.getVarByName(actions_t_i[j]))

                count += 1


            #c = (AND (c formula))
        return c







