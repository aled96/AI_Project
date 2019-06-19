class Modifier():
    
    def do_encode(self):
        pass

class LinearModifier(Modifier):

    def do_encode(self, variables, bound):
        c = []
        formula = []
        ### TODO -> KEEP attention at intial value of formula and c (since I do c = (c --) )
        #Each step one and only one action executed
        for step in range(bound):
            actions_t_i = []
            #Acquire the list of all actions negated
            for a in variables.get(step):
                actions_t_i.append(-1*variables.get(step).get(a))
            #Put one true at a time
            for i in range(len(actions_t_i)):
                actions_t_i[i] *= -1
                #formula = (OR (formula AND(actions_t_i)))
                actions_t_i[i] *= -1
            #c = (AND (c formula))
        return c







