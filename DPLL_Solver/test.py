#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  6 10:46:20 2019

@author: tac
"""
import sys, time

from formula import Clause, Variable, Formula
from dpll import Solver
from heuristics import RandomHeuristic, PureMomsHeuristic

def test_pure(inputFile):
    f = Formula(inputFile)
    h = PureMomsHeuristic(True)
    s = Solver(f, h)
    return s.run()

def test_nopure(inputFile):
    f = Formula(inputFile)
    h = PureMomsHeuristic(False)
    s = Solver(f, h)
    return s.run()
    
def test_random(inputFile):
    f = Formula(inputFile)
    h = RandomHeuristic()
    s = Solver(f, h)
    return s.run()


"""
if (__name__ == "__main__"):
    start = time.process_time()
    print("Random Test\n"+str(test_random(sys.argv[1])))
    elapsed = time.process_time() - start
    print("Evaluated in :"+ str(elapsed)+"\n")
    
    start = time.process_time()
    print("Pure Moms Test\n"+str(test_pure(sys.argv[1])))
    elapsed = time.process_time() - start
    print("Evaluated in :"+ str(elapsed)+"\n")
    
    
    start = time.process_time()
    print("Nopure Moms Test\n"+str(test_nopure(sys.argv[1])))
    elapsed = time.process_time() - start
    print("Evaluated in :"+ str(elapsed))
"""