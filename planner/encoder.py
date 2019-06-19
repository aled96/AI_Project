from translate import pddl
import utils
from formula import *
from translate import instantiate
from translate import numeric_axiom_rules
from collections import defaultdict
import numpy as np


class Encoder():

    def __init__(self, task, modifier):
        self.task = task
        self.modifier = modifier

        (self.boolean_fluents,
         self.actions,
         self.numeric_fluents,
         self.axioms,
         self.numeric_axioms) = self.ground()

        (self.axioms_by_name,
         self.depends_on,
         self.axioms_by_layer) = self.sort_axioms()

        self.mutexes = self.computeMutexes()

        self.f_mgr = FormulaMgr()

    def ground(self):
        """
        Ground action schemas:
        This operation leverages optimizations
        implemented in the parser of the
        Temporal Fast-Downward planner
        """

        (relaxed_reachable, boolean_fluents, numeric_fluents, actions,
         durative_actions, axioms, numeric_axioms,
         reachable_action_params) = instantiate.explore(self.task)

        return boolean_fluents, actions, numeric_fluents, axioms, numeric_axioms

    def sort_axioms(self):
        """
        Returns 3 dictionaries:
        - axioms sorted by name
        - dependencies between axioms
        - axioms sorted by layer
        """

        axioms_by_name = {}
        for nax in self.numeric_axioms:
            axioms_by_name[nax.effect] = nax

        depends_on = defaultdict(list)
        for nax in self.numeric_axioms:
            for part in nax.parts:
                depends_on[nax].append(part)

        axioms_by_layer, _, _, _ = numeric_axiom_rules.handle_axioms(self.numeric_axioms)

        return axioms_by_name, depends_on, axioms_by_layer

    def computeMutexes(self):
        """
        Compute mutually exclusive actions using the conditions
        we saw during lectures.

        a != a'
        Pre  intersect Del' =! 0 or
        Pre' intersect Del  =! 0
        """

        mutexes = []

        for a1 in self.actions:
            for a2 in self.actions:
                if not a1.name == a2.name:
                    precond_a1 = [str(val) for val in a1.condition]
                    precond_a2 = [str(val) for val in a2.condition]

                    del_a1 = [str(val[1]) for val in a1.del_effects]
                    del_a2 = [str(val[1]) for val in a2.del_effects]

                    intersection = [v for v in precond_a1 if v in del_a2]

                    if len(intersection) == 0 and not [a1.name, a2.name] in mutexes and not [a2.name, a1.name] in mutexes:
                        mutexes.append([a1.name, a2.name])
                    else:
                        intersection = [v for v in precond_a2 if v in del_a1]
                        if len(intersection) == 0 and not [a1.name, a2.name] in mutexes and not [a2.name, a1.name] in mutexes:
                            mutexes.append([a1.name, a2.name])

        return mutexes

    def createVariables(self):
        ### Create boolean variables for boolean fluents (at each step) ###
        self.boolean_variables = defaultdict(dict)
        count = 1
        for step in range(self.horizon + 1):
            var_at_i = defaultdict(dict)
            for fluent in self.boolean_fluents:
                var_at_i.update({str(fluent)+"@"+str(step):count})
                self.boolean_variables.update({step: var_at_i})
                self.f_mgr.mkVar(str(fluent)+"@"+str(step))
                count += 1

        ### Create propositional variables for actions ids ###
        self.action_variables = defaultdict(dict)
        for step in range(self.horizon):
            act_at_i = defaultdict(dict)
            for a in self.actions:
                act_at_i.update({a.name+"@"+str(step):count})
                self.action_variables.update({step:act_at_i})
                self.f_mgr.mkVar(a.name+"@"+str(step))
                count += 1

    def encodeInitialState(self):
        """
        Encode formula defining initial state
        """

        initial = []

        init_f = None

        for fact in self.task.init:

            if utils.isBoolFluent(fact):
                if not fact.predicate == '=':
                    if fact in self.boolean_fluents:
                        initial.append(self.boolean_variables.get(0).get(str(fact)+"@0"))
                        if init_f == None:
                            init_f = self.f_mgr.getVarByName(str(fact)+"@0")
                        else:
                            init_f = self.f_mgr.mkAnd(init_f, self.f_mgr.getVarByName(str(fact)+"@0"))

            else:
                raise Exception('Initial condition \'{}\': type \'{}\' not recognized'.format(fact, type(fact)))

        ## Close-world assumption: if fluent is not asserted
        ## in init formula then it must be set to false.

        for variable in self.boolean_variables.get(0):
            if not variable in initial:
                initial.append(-1*self.boolean_variables.get(0).get(variable))
                if init_f == None:
                    init_f = self.f_mgr.getVarByName(self.f_mgr.mkNot(variable))
                else:
                    init_f = self.f_mgr.mkAnd(init_f, self.f_mgr.mkNot(self.f_mgr.getVarByName(variable)))


        init_f.do_print()
        return initial

    def encodeGoalState(self):
        """
        Encode formula defining goal state
        """

        def encodePropositionalGoals(goal=None):

            propositional_subgoal = []

            # UGLY HACK: we skip atomic propositions that are added
            # to handle numeric axioms by checking names.
            axiom_names = [axiom.name for axiom in self.task.axioms]

            if goal is None:
                goal = self.task.goal

            n = len(self.boolean_variables) - 1

            ## Check if goal is just a single atom
            if isinstance(goal, pddl.conditions.Atom):
                if not goal.predicate in axiom_names:
                    propositional_subgoal.append(self.boolean_variables.get(n).get(str(goal)+"@"+str(n)))

            ## Check if goal is a conjunction
            elif isinstance(goal, pddl.conditions.Conjunction):
                for fact in goal.parts:
                    propositional_subgoal.append(self.boolean_variables.get(n).get(str(goal)+"@"+str(n)))

            else:
                raise Exception(
                    'Propositional goal condition \'{}\': type \'{}\' not recognized'.format(goal, type(goal)))

            return propositional_subgoal

        propositional_subgoal = encodePropositionalGoals()
        #goal = And(propositional_subgoal) #Transform in AND the list given

        #return goal
        return propositional_subgoal

    def encodeActions(self):
        """
        Encode action constraints:
        each action variable implies its preconditions
        and effects
        """

        actions = []

        for step in range(self.horizon):
            for action in self.actions:

                precondition = []
                additions = []
                deletion = []

                ## Encode preconditions
                for pre in action.condition:
                    precondition.append(self.boolean_variables.get(step).get(str(pre)+"@"+str(step)))

                ## Encode add effects (conditional supported)
                for add in action.add_effects:
                    additions.append(self.boolean_variables.get(step+1).get(str(add)+"@"+str(step+1)))

                ## Encode delete effects (conditional supported)
                for de in action.del_effects:
                    deletion.append(self.boolean_variables.get(step+1).get(str(de)+"@"+str(step+1)))
                #TODO-> Here I have the pre, add, del for the action.
                # to check how to do it
                # actions.append(Node( Node(ai) -> Add(precondition)))
                # actions.append(Node( Node(ai) -> Add(additions)))
                # actions.append(Node( Node(ai) -> Add(deletions)))

        return actions


    def encodeFrame(self):
        """
        Encode explanatory frame axioms
        """

        frame = []

        for step in range(self.horizon):
            ## Encode frame axioms for boolean fluents
            for fluent in self.boolean_fluents:
                fi = self.boolean_variables.get(step).get(str(fluent) + "@" + str(step))
                #TODO-> remember the NOT !
                fi_plus_1 = self.boolean_variables.get(step+1).get(str(fluent) + "@" + str(step+1))

                if fi < 0:
                    #IMP ( OR(fi NOT (fi+1)) OR(actions s.t. fluent is in Del)
                    pass
                else:
                    #IMP ( OR(NOT fi (fi+1)) OR(actions s.t. fluent is in Add)
                    pass

        return frame

    def encodeExecutionSemantics(self):

        try:
            return self.modifier.do_encode(self.action_variables, self.horizon)
        except:
            return self.modifier.do_encode(self.action_variables, self.mutexes, self.horizon)

    def encodeAtLeastOne(self):
        """
        For each step (AND) -> OR of every action at step i
        """
        atleastone = []
        for step in range(self.horizon):
            actions = []
            for a in self.actions:
                actions.append(a.name+"@"+str(step))
            #atleastone.append(Or(actions.append))
            pass
        return atleastone

    def encode(self, horizon):
        """
        Basic routine for bounded encoding:
        encodes initial, transition,goal conditions
        together with frame and exclusiveness/mutexes axioms

        """



        pass

    def dump(self):
        print('Dumping encoding')
        raise Exception('Not implemented yet')


class EncoderSAT(Encoder):

    def encode(self, horizon):
        self.horizon = horizon

        ## Create variables
        self.createVariables()

        ### Start encoding formula ###

        formula = defaultdict(list)

        ## Encode initial state axioms

        formula['initial'] = self.encodeInitialState()

        ## Encode goal state axioms

        formula['goal'] = self.encodeGoalState()

        ## Encode universal axioms

        formula['actions'] = self.encodeActions()

        ## Encode explanatory frame axioms

        formula['frame'] = self.encodeFrame()

        ## Encode execution semantics (lin/par)

        formula['sem'] = self.encodeExecutionSemantics()

        ## Encode at least one axioms

        formula['alo'] = self.encodeAtLeastOne()

        return formula
