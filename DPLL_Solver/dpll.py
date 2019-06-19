#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 11:32:47 2017

@author: tac
"""

class Status:
    def __init__(self, var_index, closed):
        self.var_index = var_index
        self.closed = closed

class Solver:
    def __init__(self, formula, heuristic):
        self.formula = formula
        self.choose_variable = heuristic
        self.stack = list()
        
    def run(self):
        done = False
        formula = self.formula
        while (not done):
            # Assign all unit clauses, including those that are generated by this process
            self.unit_propagate()
            if formula.is_satisfied():
                # The formula is satisfied: end of search
                done = True
            elif formula.is_contradicted():
                # The formula is contraticted: keep searching if possible, otherwise give up
                done = self.backtrack()
            else:
                # We must choose a variable and assign it tentatively
                self.choose_variable.run(formula, self.stack)
        return self.extract_assignment()

    def unit_propagate(self):
        formula = self.formula
        stack = self.stack
        # While there is at least one unit clause...
        while (len(formula.unit_cl_list) > 0):
            # ... get the unit clause 
            cl_index = formula.unit_cl_list.pop()
            cl = formula.clause_list[cl_index]
            for lit in cl.lit_list:
                # Search the variable still unassigned (if any)
                var = formula.variable_list[abs(lit)]
                if (var.value == 0):
                    # Assign the variable so as to subsume the clause
                    formula.do_eval(abs(lit), lit/abs(lit))
                    # Record the assignemnt in the stack as "closed"
                    stack.append(Status(abs(lit),True))
                    break
        return

    def backtrack(self):
        formula = self.formula
        stack = self.stack
        # Reset the empty clause list
        formula.empty_cl_list = list()
        # Go back in the stack, search for an "open" assigment
        while (len(stack) > 0):
            sr = stack.pop()
            # Get the variable index
            var_index = sr.var_index
            # The new value to assign, if any, is the opposite of the current one
            new_value = -1 * formula.variable_list[var_index].value
            # Undo the old assignment
            formula.undo_eval(var_index)
            if (not sr.closed):
                # Redo assignment with new value when possible
                formula.do_eval(var_index, new_value)
                # The assignment is now "closed": no further values to try
                stack.append(Status(var_index,True))
                # Backtracking was successful: the search must go on
                return False
        # No further backtracking is possible: the search must end
        return True

    def extract_assignment(self):
        assignment = list()
        for sr in self.stack:
            value = self.formula.variable_list[sr.var_index].value
            assignment.append(sr.var_index * value)
        return assignment



