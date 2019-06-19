#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum


#Class operator is an enum (inherits from base class Enum)
class Operator(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    IMP = "IMP"
    
#Class to represent nodes of propositional formulas as trees
class Node:
    def __init__(self, nodeid, op = None, left = None, right = None, label = None):
        self.id = nodeid                #Unique node ID
        self.op = op                    #None if it is a variable
        self.left = left                #Left child (None, for variables)
        self.right = right              #Right child (none, for variables)
        self.label = label              #An optional label (ok for encodings)
        self.refcount = 0               #Reference count
        
    #The idea is that we want to map a node into a number.
    #Problem -> many more objects than numbers -> Hash function might return same numbers for different objects -> collision (handled  
    #internally).
    def __hash__(self):
        base = 17   #We start with a prime number
        #Then apply a rule to evaluate polynomial using fields of ojects as params
        #This is equivalent to evaluate a polynomial.
        if(self.op == None):
            base = 31 * base + hash(self.id)    #hash -> building function for integers(same id <-> same hash)
        else:
            base = 31 * base + hash(self.op)
            if(self.left != None):
                base = 31 * base + hash(self.left.id)
            if(self.right != None):
                base = 31 * base + hash(self.right.id)
        return base
        
    def __eq__(self, other):
        result = (self.__class__ == other.__class__)
        if (self.op == None):
            return result and self.id == other.id
        else:
            return result and\
            self.op == other.op and\
            self.left.id == other.left.id and\
            (self.right == None or self.right.id == other.right.id)

    def do_print(self):
        # Internal function to prinr IDs
        def get_id(i, flag):
            if (flag):
                return ":" + str(i) 
            else:
                return ""
        if(self.op == None):
            print("v"+str(self.id)),
        else:
            print("("+self.op.name+" "),
            if(self.left != None):
                self.left.do_print()
            if(self.right != None):
                self.right.do_print()
            print(")"),
    
#Class to handle subformula sharing and formula building
class FormulaMgr:
    #We need to check if a formula is already in the formula manager or not, in order to not waste space
    def __init__(self):
        self.lastId = -1
        self.recycleIds = list()        #Some formula can be destroyed in NNF convertion (Recycle Id)
        self.node2id = dict()       
        self.id2node = list()
        self.name2id = dict()
        
    def getId(self):
        if(len(self.recycleIds) == 0):
            #Create a new Id
            self.id2node.append(None)
            self.lastId += 1
            return self.lastId
        else:
            #Recycle existing Id
            return self.recycleIds.pop()
    
    
    # Dispose of a node when its reference count reaches 1
    # or reduce its reference count
    def dispose(self, node):
        if (node.refcount > 1):
            # Reduce the reference count of the children (if any)
            if (node.left != None):
                node.left.refcount -= 1
            if (node.right != None):
                node.right.refcount -= 1
            # If the node has a label, remove it from the index
            if (node.label != None):
                self.name2id.pop(node.label)
            # Remove the node from all other indexes
            self.node2id.pop(node)
            self.id2node[node.id] = None
            # The id can be recycled 
            self.recycleIds.append(node.id)
        else:
            node.refcount -= 1
            
        
    def mkVar(self, name = None):
        #I don't want to duplicate, need to check if exists or not
        if(name != None):
            nodeid = self.name2id.get(name)
            if( nodeid != None):
                return self.id2node[nodeid]
        #Otherwise -> I need to create a new variable
        nodeid = self.getId()
        node = Node(nodeid, label = name)
        self.node2id[node] = nodeid
        self.id2node[nodeid] = node
        #if name was given:
        if(name != None):
            self.name2id[name] = nodeid
            
        return node
        
    # Get the variable node using the label as a reference
    def getVarByName(self, name):
        if (name != None):
            return self.id2node[self.name2id.get(name)]
        else:
            return None
    
    # Get the variable node using the unique id as a reference
    def getVarById(self, varid):
        if (varid <= self.lastId):
            return self.id2node[varid]
        else:
            return None
    

    def mkOp(self, temp):
        #Needs to look in the table and see if such node (temp) exists
        nodeid = self.node2id.get(temp)
        if(nodeid != None):
            #If already there, I take it and incremente the reference count
            node = self.id2node[nodeid]
            node.refcount += 1
            return node
        else:
            #Otherwise I will create it
            nodeid = self.getId()
            temp.id = nodeid
            self.id2node[nodeid] = temp
            self.node2id[temp] = nodeid
            return temp
            
    
    def mkAnd(self, f, g):
        #Create temp Node and check if it is alreadt saved or not
        temp = Node(0, op=Operator.AND, left = f, right = g)
        return self.mkOp(temp)
        
    def mkOr(self, f, g):
        temp = Node(0, op=Operator.OR, left = f, right = g)
        return self.mkOp(temp)
        
    def mkNot(self, f):
        temp = Node(0, op=Operator.NOT, left = f)
        return self.mkOp(temp)
        
    def mkImp(self, f, g):
        temp = Node(0, op=Operator.IMP, left = f, right = g)
        return self.mkOp(temp)
        
        
        
#Class to handle nnf Conversion
class NnfConversion:
    
    def __init__(self, mgr):
        self.manager = mgr
        
    def do_conversion(self, node):
        if(node.op != None): #Otherwise no sense
            if(node.op == Operator.NOT):    #If main operator in NOT -> convert into the opposite
                temp = self.convert(node.left, -1)
                self.manager.dispose(node)
                node = temp
            else:
                node = self.convert(node,1)
        return node
                
    def convert(self, node, polarity):
        if(node.op == None): #If I am applying to a variable
            if(polarity > 0):
                return node
            else:
                return self.manager.mkNot(node)
        elif(node.op == Operator.NOT):  #If I have a NOT
            temp = self.convert(node.left, -1*polarity) #So the opposite
            self.manager.dispose(node) #I remove the node
            return temp
        elif (node.op == Operator.AND):
            if (polarity < 0):
                left = self.convert(node.left, -1)
                right = self.convert(node.right, -1)
                return self.manager.mkOr(left, right)
            else:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, 1)
                return self.manager.mkAnd(left, right)
        elif (node.op == Operator.OR):
            if (polarity < 0):
                left = self.convert(node.left, -1)
                right = self.convert(node.right, -1)
                return self.manager.mkAnd(left, right)
            else:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, 1)         
                return self.manager.mkOr(left, right)
        elif (node.op == Operator.IMP):
            if (polarity < 0):
                left = self.convert(node.left, 1)
                right = self.convert(node.right, -1)
                return self.manager.mkAnd(left, right)
            else:
                left = self.convert(node.left, 1)
                right = self.convert(node.right, 1)
                return self.manager.mkImply(left, right)
        else:
            # This cannot happen
            assert True
            
#Class to handle cnf conversion
#Assume to be converted into NNF first
class CnfConversion:
    
    def __init__(self, mgr):
        self.clauses = list()
        self.definitions = dict()
        self.manager = mgr
        
    # Assumes that the formula is in negative normal form
    def do_conversion(self, node):
        # Fail if the formula is not in NNF
        assert (node.op != Operator.NOT) or (node.left.op == None)
    
        # Add the unit clause representing the formula itself
        self.clauses.append([node.id])
        if (node.op != None):
            self.convert(node)
        return
    
    def get_clauses(self):
        return self.clauses
    
    def convert(self, node):
        # Fail if the formula is not in NNF
        assert (node.op != Operator.NOT) or (node.left.op == None)
        # Nothing to do if a literal is reached (variable or negation thereof) 
        if (node.op == None) or (node.op == Operator.NOT):
            return
        # An operator: AND, OR, IMP: add the definitions and propagate 
        # If the subformula was already visited, no need to visit again
        self.add_definitions(node)
        if (self.definitions.get(node.left.id) == None):
            self.convert(node.left)
        if (self.definitions.get(node.right.id) == None):
            self.convert(node.right)
        
        
    def add_definitions(self, node):
        def_clauses = list()
        # Local alias for negation function
        neg = self.neg
        # The literal corresponding to the formula
        l = node.id
        # The literal corresponding to the left operand
        # Negations must be applied to variables only
        if (node.left.op == Operator.NOT):
            assert(node.left.left.op == None)
            l1 = neg(node.left.left.id)
        else:
            l1 = node.left.id
        # The literal corresponding to the right operand
        # Negations must be applied to variables only
        if (node.right.op == Operator.NOT):
            assert(node.right.left.op == None)
            l2 = neg(node.right.left.id)
        else:
            l2 = node.right.id
        if (node.op == Operator.AND):
            def_clauses.append([l, neg(l1), neg(l2)])
            def_clauses.append([neg(l), l1])
            def_clauses.append([neg(l), l2])
        elif (node.op == Operator.OR):
            def_clauses.append([neg(l), l1, l2])
            def_clauses.append([l, neg(l1)])
            def_clauses.append([l, neg(l2)])
        elif (node.op == Operator.IMP):
            def_clauses.append([neg(l), neg(l1), l2])
            def_clauses.append([l, l1])
            def_clauses.append([l, neg(l2)])
            pass
        else:
            # This cannot happen
            assert True
        self.definitions[node.id] = def_clauses
        self.clauses.extend(def_clauses)
        
    def neg(self, id):
        return int(id * -1)
        
"""
if __name__ == "__main__":
    mgr = FormulaMgr()
    # Test creation of variables
    v1 = mgr.mkVar()
    v2 = mgr.mkVar()
    v3 = mgr.mkVar()
    # Test creation of formulas
    print(" f:")
    f = mgr.mkAnd(v1,v2)
    f.do_print()
    f_not = mgr.mkNot(f)
    print("\n g:")
    g = mgr.mkOr(v1,v2)
    g.do_print()   
    g_not = mgr.mkNot(g)
    print("\n h:")
    h = mgr.mkImply(v1,v2)
    h.do_print()
    h_not = mgr.mkNot(h)
    s = mgr.mkOr(g,h)
    s = mgr.mkOr(f,s)
    s_not = mgr.mkNot(s)    
    print("\n s:")
    s.do_print()
    print("\n s (neg):")
    s_not.do_print()
    s_not_not = mgr.mkNot(s_not)    
    print("\n s (neg, neg):")
    s_not_not.do_print()
    print("\n")
    
    # Test negation normal form
    nnfize = NnfConversion(mgr)
    f_nnf = nnfize.do_conversion(f)
    print("\n f_nnf:")
    f_nnf.do_print()
    f_nnf = nnfize.do_conversion(f_not)
    print("\n f_nnf (neg):")
    f_nnf.do_print()
    g_nnf = nnfize.do_conversion(g)
    print("\n g_nnf:")
    g_nnf.do_print()
    g_nnf = nnfize.do_conversion(g_not)
    print("\n g_nnf (neg):")
    g_nnf.do_print()
    print("\n h_nnf:")
    h_nnf = nnfize.do_conversion(h)
    h_nnf.do_print()
    h_nnf = nnfize.do_conversion(h_not)
    print("\n h_nnf (neg):")
    h_nnf.do_print()
    s_nnf = nnfize.do_conversion(s)
    print("\n s_nnf:")
    s_nnf.do_print()
    s_nnf = nnfize.do_conversion(s_not)
    print("\n s_nnf (neg):")
    s_nnf.do_print()
    s_nnf = nnfize.do_conversion(s_not_not)
    print("\n s_nnf (neg,neg):")
    s_nnf.do_print()
    print("\n")    
    
    # Test CNF conversion
    cnfize_s = CnfConversion(mgr)
    cnfize_s.do_conversion(s)
    print("\n s (with ids)")
    s.do_print(True)
    print("\n s in CNF:")
    print(cnfize_s.get_clauses())
    
    # Test CNF conversion with repeated subformulas
    r = mgr.mkAnd(s,s)
    cnfize_r = CnfConversion(mgr)
    cnfize_r.do_conversion(r)
    print("\n r (with ids)")
    r.do_print(True)
    print("\n r in CNF:")
    print(cnfize_r.get_clauses())
    """
