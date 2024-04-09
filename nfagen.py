#!/usr/bin/env python3
from node import Node

class NFA:
    def __init__(self, alphabet, lam):
        self.alphabet = alphabet
        self.lam = lam
        # states need to be hashed by key, not stored in list
        # start with two states, 0 and 1, 1 is accepting
        # 1 will be the only accepting state
        self.L = []
        self.T = []
        # initialize L
        for i in range(2):
            row = []
            for j in range(2):
                row.append(False)
            self.L.append(row)
        # initialize T
        for i in range(2):
            row = {}
            for c in self.alphabet:
                row[c] = "E"
            self.T.append(row)
        
    def add_state(self):
        for i in range(len(self.L)):
            self.L[i].append(False)
        self.L.append([False]*(len(self.L)+1))

        row = {}
        for c in self.alphabet:
            row[c] = "E"
        self.T.append(row)
        return len(self.L) - 1
    
    def add_lambda(self, src, dest):
        self.L[src][dest] = True

    def add_edge(self, src, dest, char):
        self.T[src][char] = dest

    def lambda_wrap(self, src, dest, child):
        before = self.add_state()
        after = self.add_state()
        self.add_lambda(src, before)
        self.add_lambda(after, dest)
        self.process_child(before, after, child)

    def process_child(self, src, dest, child):
        if child.kind == "SEQ":
            self.node_seq(src, dest, child)
        elif child.kind == "ALT":
            self.node_alt(src, dest, child)
        elif child.kind == "range":
            self.node_range(src, dest, child)
        elif child.kind == "kleene":
            self.node_kleene(src, dest, child)
        elif child.value == "lambda":
            self.leaf_lambda(src, dest, child)
        elif child.kind == "dot":
            self.leaf_dot(src, dest, child)
        elif child.value in self.alphabet:
            self.leaf_char(src, dest, child)
    
    def leaf_char(self, src, dest, child):
        self.add_edge(src, dest, child.value)
    
    def leaf_lambda(self, src, dest, child):
        self.add_lambda(src, dest)

    def node_seq(self, src, dest, seq):
        for child in seq.children:
            childDest = self.add_state()
            self.lambda_wrap(src, childDest, child)
            src = childDest
        self.add_lambda(childDest, dest)

    def node_alt(self, src, dest, alt):
        for child in alt.children:
            childDest = self.add_state()
            self.lambda_wrap(src, childDest, child)
            self.add_lambda(childDest, dest)

    def node_range(self, src, dest, child):
        children = child.children
        for val in range(ord(children[0].value), ord(children[1].value)+1):
            if chr(val) in self.alphabet:
                self.add_edge(src, dest, chr(val))
    
    def node_kleene(self, src, dest, kleene):
        # kleene will only ever have one child
        self.lambda_wrap(src, dest, kleene.children[0])
        self.add_lambda(src, dest)
        self.add_lambda(dest, src)

    def leaf_dot(self, src, dest, child):
        for char in self.alphabet:
            self.add_edge(src, dest, char)
    
    def select_lambda(self):
        lam = chr(0)
        while lam in self.alphabet:
            lam = chr(int(lam) + 1)
        return lam

    def alphabet_encode(self, c):
        # operates on a single character
        return str(hex(ord(c)))[1:]

    def __str__(self):
        # lam = self.select_lambda()
        output = ""
        output += str(len(self.L))
        output += " "
        output += self.alphabet_encode(self.lam)
        output += " "
        for c in self.alphabet:
            output += self.alphabet_encode(c)
            output += " "
        output += "\n"
        for i in range(len(self.T)):
            for c in self.T[i]:
                if self.T[i][c] != "E":
                    output += "-"
                    output += " "
                    output += str(i)
                    output += " "
                    output += str(self.T[i][c])
                    output += " "
                    output += self.alphabet_encode(c)
                    output += "\n"
        for i in range(len(self.L)):
            for j in range(len(self.L)):
                if self.L[i][j]:
                    output += "-"
                    output += " "
                    output += str(i)
                    output += " "
                    output += str(j)
                    output += " "
                    output += self.alphabet_encode(self.lam)
                    output += "\n"
        output += "+ 1 1"
        
        return output

