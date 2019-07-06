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
                        initial.append(str(fact)+"@0")
                        if init_f is None:
                            init_f = self.f_mgr.getVarByName(str(fact)+"@0")
                        else:
                            init_f = utils.add_to_manager(self.f_mgr, init_f, self.f_mgr.getVarByName(str(fact)+"@0"), 2)

            else:
                raise Exception('Initial condition \'{}\': type \'{}\' not recognized'.format(fact, type(fact)))

        ## Close-world assumption: if fluent is not asserted
        ## in init formula then it must be set to false.

        for variable in self.boolean_variables.get(0):
            if not variable in initial:
                initial.append(-1*self.boolean_variables.get(0).get(variable))
                if init_f is None:
                    init_f = self.f_mgr.getVarByName(self.f_mgr.mkNot(variable))
                else:
                    init_f = utils.add_to_manager(self.f_mgr, init_f, self.f_mgr.mkNot(self.f_mgr.getVarByName(variable)), 2)


        return init_f

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
                    propositional_subgoal.append(str(goal)+"@"+str(n))

            ## Check if goal is a conjunction
            elif isinstance(goal, pddl.conditions.Conjunction):
                for fact in goal.parts:
                    propositional_subgoal.append(str(fact)+"@"+str(n))

            else:
                raise Exception(
                    'Propositional goal condition \'{}\': type \'{}\' not recognized'.format(goal, type(goal)))

            return propositional_subgoal

        propositional_subgoal = encodePropositionalGoals()

        # Transform in AND the list given
        goal = None
        for p in propositional_subgoal:
            if goal is None:
                goal = self.f_mgr.getVarByName(p)
            else:
                goal = utils.add_to_manager(self.f_mgr, goal, self.f_mgr.getVarByName(p), 2)

        #return goal
        return goal

    def encodeActions(self):
        """
        Encode action constraints:
        each action variable implies its preconditions
        and effects
        """

        actions = None

        for step in range(self.horizon):
            for action in self.actions:
                p = None
                a = None
                d = None
                ## Encode preconditions
                for pre in action.condition:
                    if(p is None):
                        if pre.negated:
                            p = self.f_mgr.mkNot(self.f_mgr.getVarByName(str(pre) + "@" + str(step)))
                        else:
                            p = self.f_mgr.getVarByName(str(pre)+"@"+str(step))
                    else:
                        if pre.negated:
                            p = utils.add_to_manager(self.f_mgr, p, self.f_mgr.mkNot(self.f_mgr.getVarByName(str(pre) + "@" + str(step))),2)
                        else:
                            p = utils.add_to_manager(self.f_mgr, p, self.f_mgr.getVarByName(str(pre)+"@"+str(step)), 2)

                if actions is None:
                    actions = utils.add_to_manager(self.f_mgr, self.f_mgr.getVarByName(action.name + "@" + str(step)), p, 3)
                else:
                    actions = utils.add_to_manager(self.f_mgr, self.f_mgr.mkImp(self.f_mgr.getVarByName(action.name + "@" + str(step)), p), actions, 2)

                ## Encode add effects (conditional supported)
                for add in action.add_effects:
                    if(a is None):
                        a = self.f_mgr.getVarByName(str(add[1])+"@"+str(step+1))
                    else:
                        a = utils.add_to_manager(self.f_mgr, self.f_mgr.getVarByName(str(add[1])+"@"+str(step+1)), a, 2)

                if actions is None:
                    actions = self.f_mgr.mkImp(self.f_mgr.getVarByName(action.name + "@" + str(step)), a)
                else:
                    actions = utils.add_to_manager(self.f_mgr, self.f_mgr.mkImp(self.f_mgr.getVarByName(action.name + "@" + str(step)), a), actions, 2)

                ## Encode delete effects (conditional supported)
                for de in action.del_effects:
                    if(d is None):
                        d = self.f_mgr.mkNot(self.f_mgr.getVarByName(str(de[1])+"@"+str(step+1)))
                    else:
                        d = utils.add_to_manager(self.f_mgr, d, self.f_mgr.mkNot(self.f_mgr.getVarByName(str(de[1])+"@"+str(step+1))), 2)

                if actions is None:
                    actions = self.f_mgr.mkImp(self.f_mgr.getVarByName(action.name + "@" + str(step)), d)
                else:
                    actions = utils.add_to_manager(self.f_mgr, self.f_mgr.mkImp(self.f_mgr.getVarByName(action.name + "@" + str(step)), d), actions, 2)
        return actions


    def encodeFrame(self):
        """
        Encode explanatory frame axioms
        """
        frame_pl = None
        for step in range(self.horizon):
            ## Encode frame axioms for boolean fluents
            for fluent in self.boolean_fluents:
                fi = str(fluent) + "@" + str(step)
                fi_plus_1 = str(fluent) + "@" + str(step+1)


                #TODO -> make better
                actions_in_or = None
                fluents_and = None

                #fi and NOT fi+1
                fluents_and = utils.add_to_manager(self.f_mgr, self.f_mgr.getVarByName(fi), self.f_mgr.mkNot(self.f_mgr.getVarByName(fi_plus_1)), 2)

                for a in self.actions:
                    for d in a.del_effects:
                        if d[1] == fluent:
                            if(actions_in_or is None):
                                actions_in_or = self.f_mgr.getVarByName(a.name+"@"+str(step))
                            else:
                                actions_in_or = utils.add_to_manager(self.f_mgr, actions_in_or, self.f_mgr.getVarByName(a.name+"@"+str(step)), 1)
                            break

                # IMP ( AND(NOT(fi) fi+1), OR(actions s.t. fluent is in Add/Del))
                if (actions_in_or is not None):
                    if frame_pl is None:
                        frame_pl = self.f_mgr.mkImp(fluents_and, actions_in_or)
                    else:
                        frame_pl = utils.add_to_manager(self.f_mgr, self.f_mgr.mkImp(fluents_and, actions_in_or), frame_pl, 2)


                #NOT fi and fi+1
                fluents_and = utils.add_to_manager(self.f_mgr, self.f_mgr.mkNot(self.f_mgr.getVarByName(fi)), self.f_mgr.getVarByName(fi_plus_1), 2)

                actions_in_or = None
                for a in self.actions:
                    for add in a.add_effects:
                        if add[1] == fluent:
                            if(actions_in_or is None):
                                actions_in_or = self.f_mgr.getVarByName(a.name+"@"+str(step))
                            else:
                                actions_in_or = utils.add_to_manager(self.f_mgr, actions_in_or, self.f_mgr.getVarByName(a.name+"@"+str(step)), 1)
                            pass


                # IMP ( AND(NOT(fi) fi+1), OR(actions s.t. fluent is in Add/Del))
                if (actions_in_or is not None):
                    if frame_pl is None:
                        frame_pl = self.f_mgr.mkImp(fluents_and, actions_in_or)
                    else:
                        frame_pl = utils.add_to_manager(self.f_mgr, frame_pl, self.f_mgr.mkImp(fluents_and, actions_in_or), 2)

        return frame_pl

    def encodeExecutionSemantics(self):

        try:
            return self.modifier.do_encode(self.action_variables, self.horizon, self.f_mgr)
        except:
            return self.modifier.do_encode(self.action_variables, self.mutexes, self.horizon, self.f_mgr)

    def encodeAtLeastOne(self):
        """
        For each step (AND) -> OR of every action at step i
        """
        atleastone = None
        for step in range(self.horizon):

            actions_or = None

            #OR of all the actions at time i
            for a in self.actions:
                if actions_or is None:
                    actions_or = self.f_mgr.getVarByName(a.name+"@"+str(step))
                else:
                    actions_or = utils.add_to_manager(self.f_mgr, actions_or, self.f_mgr.getVarByName(a.name+"@"+str(step)), 1)

            #AND of the ORs
            if atleastone is None:
                atleastone = actions_or
            else:
                atleastone = utils.add_to_manager(self.f_mgr, atleastone, actions_or, 2)
        return atleastone

    def dump(self):
        print('Dumping encoding')
        raise Exception('Not implemented yet')


class EncoderSAT(Encoder):

    def encode(self, horizon):
        """
        Basic routine for bounded encoding:
        encodes initial, transition,goal conditions
        together with frame and exclusiveness/mutexes axioms

        """
        self.horizon = horizon

        ## Create variables
        self.createVariables()

        ### Start encoding formula ###

        formula = defaultdict(list)

        ## Encode initial state axioms

        #TODO -> remove all print
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
        #Already in CNF (ANDs of ORs)
        formula['alo'] = self.encodeAtLeastOne()

        return formula

    def convert_CNF(self, formula):

        nnf_conv = NnfConversion(self.f_mgr)
        cnf_conv = CnfConversion(self.f_mgr)

        #TODO -> make improvements, we have that Initial, Goal and AtLeastOne -> In CNF
        formula_collapsed = formula['initial']
        formula_collapsed = utils.add_to_manager(self.f_mgr, formula_collapsed, formula['goal'], 2)
        formula_collapsed = utils.add_to_manager(self.f_mgr, formula_collapsed, formula['actions'], 2)
        formula_collapsed = utils.add_to_manager(self.f_mgr, formula_collapsed, formula['frame'], 2)
        formula_collapsed = utils.add_to_manager(self.f_mgr, formula_collapsed, formula['sem'], 2)
        formula_collapsed = utils.add_to_manager(self.f_mgr, formula_collapsed, formula['alo'], 2)

        #Convert in NNF
        formula_nnf = nnf_conv.do_conversion(formula_collapsed)

        #Convert in CNF
        formula_cnf = cnf_conv.do_conversion(formula_nnf)

        return  formula_cnf