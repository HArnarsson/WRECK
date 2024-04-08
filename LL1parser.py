#!/usr/bin/env python3

import sys
from collections import namedtuple

# lambda_symbol = '\u03BB'

class Node:
    def __init__(self, kind, val=None):
        self.children = []
        self.parent = None
        self.kind = kind
        self.value = val

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def replace_all_children(self, newChild):
        self.children.clear()
        self.add_child(newChild)

    def has_child_of_kind(self, kind):
        for child in self.children:
            if child.kind == kind:
                return True
        return False

    def get_child_of_kind(self, kind):
        for child in self.children:
            if child.kind == kind:
                return child
        print(f'ERROR {self} does not have any {kind} children')
    
    def replace_self(self, replacement):
        # don't change parent value
        # self.children = replacement.children.copy()
        self.children.clear()
        self.adopt_children(replacement.children)
        self.kind = replacement.kind
        self.value = replacement.value

    def copy(self):
        newNode = Node(kind=self.kind, val=self.value)
        newNode.children = self.children.copy()
        newNode.parent = self.parent
        return newNode
    
    def adopt_children(self, newChildren):
        for child in newChildren:
            child.parent = self
            self.children.append(child)

    def remove_child(self, kind):
        newChildren = []
        for child in self.children:
            if child.kind == kind:
                continue
            else:
                newChildren.append(child)
        self.children = newChildren

    def NUCLEUS(self):
        if self.has_child_of_kind('CHARRNG'):
            charrngChild = self.get_child_of_kind('CHARRNG')

            if charrngChild.has_child_of_kind('char'):
                grandchild = charrngChild.get_child_of_kind('char')
                rangeNode = Node(kind='range')
                charNode = self.get_child_of_kind('char')
                rangeNode.add_child(charNode)
                rangeNode.add_child(grandchild)
                self.replace_all_children(rangeNode)
                return self

            if charrngChild.has_child_of_kind('\u03BB'):
                self.children.remove(charrngChild)
                return self
            
        elif self.has_child_of_kind('dot'):
            dotChild = self.get_child_of_kind('dot')
            self.replace_self(dotChild)
            return self
        
        elif self.children[0].kind == 'open':
            altNode = self.children[1]
            self.replace_self(altNode)
            return self
        
        elif len(self.children) == 1:
            
            replacement = self.children[0]
            self.replace_self(replacement)
        
        return self
    
    def ATOM(self):
        if self.has_child_of_kind('ATOMMOD'):
            child = self.get_child_of_kind('ATOMMOD')
            if child.has_child_of_kind('\u03BB'):
                leftChild = self.children[0]
                if leftChild.children:
                    replacement = leftChild.children[0]
                else:
                    replacement = leftChild
                # replacement = leftChild.children[0]
                self.replace_self(replacement)
                return self
            if child.has_child_of_kind('kleene'):
                newAtom = Node(kind='kleene')
                newAtom.add_child(self.children[0].children[0]) # leftmost child of the leftmost child
                self.replace_self(newAtom)
                return self
            if child.has_child_of_kind('plus'):
                newAtom = Node(kind='SEQ')
                newAtom.add_child(self.children[0].children[0]) 
                newKleen = Node(kind='kleene')
                newKleen.add_child((self.children[0].children[0]).copy())
                newAtom.add_child(newKleen)
                self.replace_self(newAtom)
                return self
        return self

    def SEQLIST(self):
        parent = self.parent
        if self.has_child_of_kind('\u03BB'):
            parent.children.remove(self)
            return parent
        elif parent.kind == 'SEQLIST':
            grandkids = self.children
            # parent.children.remove(self)
            parent.remove_child('SEQLIST')
            parent.adopt_children(grandkids)
            return parent 
        if len(self.children) == 1:
            replacement = self.children[0]
            self.replace_self(replacement)           
        return self

    def SEQ(self):
        while self.has_child_of_kind('SEQLIST'):
            child = self.get_child_of_kind('SEQLIST')
            grandKids = child.children
            # self.children.remove(child)
            self.remove_child('SEQLIST')
            self.adopt_children(grandKids)
        # don't know if this is necessary just here to deal with the plus logic
        if self.has_child_of_kind('SEQ'):
            seqChild = self.get_child_of_kind('SEQ')
            grandchildren = seqChild.children
            # self.children.remove(seqChild)
            self.remove_child('SEQ')
            self.adopt_children(grandchildren)
        elif len(self.children) == 1:
            replacement = self.children[0]
            self.replace_self(replacement)
        return self

    def ALTLIST(self):
        parent = self.parent
        if parent.kind == 'ALTLIST':
            grandkids = self.children
            # parent.children.pop(self)
            parent.remove_child('ALTLIST')
            parent.adopt_children(grandkids)
            return parent
        if len(self.children) == 1 and self.has_child_of_kind('\u03BB'):
            # parent = self.parent
            parent.remove_child('ALTLIST')
            return parent
        return self
    
    def ALT(self):
        if self.has_child_of_kind('ALTLIST'):
            child = self.get_child_of_kind('ALTLIST')
            if not child.has_child_of_kind('pipe'):
                replacement = self.children[0]
                self.replace_self(replacement)
                return self
        if len(self.children) == 1:
            replacement = self.children[0]
            self.replace_self(replacement)
            return self
        return self

    def RE(self):
        return self.children[0]
    
    def sdt_procedure(self):
        # print(f'initiating sdt procedure with {self}')
        # print(f'self: {self}')
        # print(f'children: {self.children}')
        # print(f'parent: {self.parent}')
        if self.kind == 'NUCLEUS':
            return(self.NUCLEUS())
        if self.kind == 'ATOM':
            return(self.ATOM())
        elif self.kind == 'SEQ':
            return(self.SEQ())
        if self.kind == 'SEQLIST':
            return (self.SEQLIST())
        elif self.kind == 'ALT':
            return(self.ALT())
        elif self.kind == 'ATLIST':
            return(self.ALTLIST())
        elif self.kind == 'RE':
            return(self.RE())
        else:
            return self
    
    def __repr__(self):
        printStr = f'({self.kind}, {self.value})'
        return printStr

class CFG:
    def __init__(self):
        self.productionRules = {} 
        self.productionRulesByKey = {}
        self.startSymbol = ""
        self.nonTerminals = set() 
        self.terminals = set() 
        self.lastSeen = None
        self.llt = None

    def __str__(self):
        output = "Grammar Non-Terminals\n"
        for symbol in sorted(self.nonTerminals):
            output += symbol + ", "
        output = output[:-2] + "\n"
 
        output += "Grammar Symbols\n"
        for symbol in sorted(self.terminals):
            output += symbol + ", "
        for symbol in sorted(self.nonTerminals):
            if symbol != "lambda":
                output += symbol + ", "
        output = output[:-2] + "\n"

        output += "\n"
        output += "Grammar Rules\n"
        # probably wnat to print startSymbol here first
        i = 1 
        for nt in self.productionRules.keys():
            for rule in self.productionRules[nt]:
                output += f"({i})\t{nt} -> {' '.join(rule) if rule != [] else 'lambda'}\n"
                i += 1
        output += "\n"
        output += f"Grammar Start Symbol or Goal: {self.startSymbol}"
        return output
        

    def is_terminal(self, symbol):
        for c in symbol:
            if c.isupper():
                return False
        return True

    def add_production_rule(self, rule):
        ARROW = "->"
        tmp = rule.split(ARROW) 
        if len(tmp) == 2:
            # case where we start with NonTerminal -> rules
            nonTerminal = tmp[0].strip()
            rules = tmp[1].strip()
            self.nonTerminals.add(nonTerminal)
            self.lastSeen = nonTerminal
            rules = rules.split("|")
            if "$" in rules[-1]:
                self.startSymbol = nonTerminal
        else:
            # case where we start with |, use lastSeen as lhs
            nonTerminal = self.lastSeen
            rules = tmp[0].split("|")[1:]

        if not nonTerminal in self.productionRules.keys():
            self.productionRules[nonTerminal] = []

        for rule in rules:
            if rule.strip() == "lambda":
                self.productionRules[nonTerminal].append([])
            else:
                self.productionRules[nonTerminal].append(rule.strip().split())
        
        for rule in self.productionRules[nonTerminal]:
            for symbol in rule:
                if self.is_terminal(symbol):
                    self.terminals.add(symbol)
                else:
                    self.nonTerminals.add(symbol)

    def dtl_helper(self, nonTerminal, T):
        for prod_rule in self.productionRules[nonTerminal]:
            if prod_rule in T:
                continue
            if prod_rule == []:
                return True
            if any(self.is_terminal(symbol) for symbol in prod_rule):
                continue
            allDeriveLambda = True
            for symbol in prod_rule:
                T.append(prod_rule)
                allDeriveLambda = self.dtl_helper(symbol, T)
                T.pop()
                if not allDeriveLambda:
                    break
            if allDeriveLambda:
                return True
        return False

    def derives_to_lambda(self, nonTerminal):
        if self.is_terminal(nonTerminal):
            return False
        return self.dtl_helper(nonTerminal, [])
    
    def first_helper(self, sequence, T):
        if sequence == []:
            return (set(), T)
        X = sequence[0]
        if self.is_terminal(X) or X == "$":
            tmp = set()
            tmp.add(X)
            return (tmp, T)

        F = set()

        if self.derives_to_lambda(X) and len(sequence) > 1:
            G, I = self.first_helper(sequence[1:], T)
            F = F.union(G)

        if X not in T:
            T.add(X)
            for prod_rule in self.productionRules[X]:
                # I not used
                G, I = self.first_helper(prod_rule, T)
                F = F.union(G)

        return F, T

    def first_set(self, symbol):
        return self.first_helper([symbol], set())[0]
    
    def find_pi(self, A):
        keys = [] 
        for k in self.productionRules.keys():
            for prod_rule in self.productionRules[k]:
                if A in prod_rule:
                    keys.append((k, prod_rule[prod_rule.index(A):]))
        return keys

    def follow_helper(self, A, T):
        if A in T:
            return set(), T
        
        T.add(A)
        F = set()
        for (k, pi) in self.find_pi(A):
            if len(pi) > 1:
                for symbol in pi[1:]:
                    F = F.union(self.first_set(symbol))
                    if not self.derives_to_lambda(symbol):
                        break
            # check if rest derives to lambda
            rest_to_lambda = True
            for symbol in pi[1:]:
                if self.derives_to_lambda(symbol):
                    continue
                else:
                    rest_to_lambda = False
                    break
            if len(pi) == 1 or rest_to_lambda:
                G, I = self.follow_helper(k, T)
                F = F.union(G)

        return F, T


    def follow_set(self, A):
        return self.follow_helper(A, set())[0]
    
    def is_pairwise_disjoint(self, lhs):
        sett = set()
        for rhs in self.productionRules[lhs]:
            for symbol in self.predict_set(lhs, rhs):
                if symbol in sett:
                    return False
                sett.add(symbol)
        return True

    def is_ll1(self):
        for lhs in self.productionRules:
            if not self.is_pairwise_disjoint(lhs):
                return False
        return True

    def predict_set(self, lhs, rhs):
        F = set()
        allDerivesToLambda = True
        for symbol in rhs:
            F = F.union(self.first_set(symbol))
            if self.derives_to_lambda(symbol):
                continue
            else:
                allDerivesToLambda = False
                break

        if allDerivesToLambda:
            F = F.union(self.follow_set(lhs))
        return F

    def generate_llt(self):
        if not self.is_ll1():
            print("Table is not LL(1), exiting...")
            sys.exit(1)
        self.llt = {}
        i = 1 
        for nonTerminal in self.nonTerminals:
            self.llt[nonTerminal] = {}
            for terminal in self.terminals:
                self.llt[nonTerminal][terminal] = None 
        for lhs in self.productionRules:
            for rhs in self.productionRules[lhs]:
                for symbol in self.predict_set(lhs,rhs):
                    self.llt[lhs][symbol] = i
                self.productionRulesByKey[i] = (lhs, rhs)
                i += 1
    
    def parse(self, ts):
        # LL(1) Parser
        T = Node("root")
        current = T
        K = []
        K.append(self.startSymbol)
        while len(K) > 0:
            x = K.pop()
            if x in self.nonTerminals:
                if not self.llt[x][ts.peek()]:
                    print(self.llt[x])
                    print(f"Unexpected value received from token stream: {ts.peek()}, exiting...")
                    sys.exit(1)
                else:
                    p = self.productionRulesByKey[self.llt[x][ts.peek()]]
                    K.append("*")
                    R = p[1].copy()
                    if R == []:
                        K.append('\u03BB')
                    while len(R) > 0:
                        K.append(R.pop())
                    current.add_child(Node(x))
                    current = current.children[len(current.children)-1] 
            elif x in self.terminals or x == '\u03BB' or x == 'lambda':
                if x in self.terminals:
                    if x != ts.peek():
                        print(f"Value between token stream and expected value don't match. val:{x}, ts:{ts.peek()}, exiting...")
                        sys.exit(1)
                    x = ts.pop()
                else: value = None   
                current.add_child(Node(kind=x, val=value))
                # current.add_child(Node(x))
            elif x == "*":
                if current.kind == 'root':
                    return current.children[0]
                else:
                    current = current.sdt_procedure()
                    current = current.parent
                    # current = current.sdt_procedure()
        return current.children[0]

Token = namedtuple('Token', ['type', 'value'])

class TokenStream():
    def __init__(self):
        self.tokens = []

    def addToken(self, token):
        self.tokens.append(token)

    def peek(self):
        if self.tokens: return self.tokens[0].type
        else: return '$'
    
    def pop(self):
        if self.tokens: return self.tokens.pop(0).type
        else: return '$'

    def __str__(self):
        printStr = ''
        for token in self.tokens:
            printStr += token.type + ' ' + token.value + '\n'
        return printStr

class Lexer():
    def __init__(self):
        self.escapedChars = {'\|' : Token('char', '|'), '\*' : Token('char', '*'), '\+' : Token('char', '+'), '\.' : Token('char', '.'), 
                             '\(' : Token('char', '('), '\)' : Token('char', ')'), '\-' : Token('char', '-'), '\s' : ('char', 'x20'), 
                             '\n' : Token('char', 'x0a'), '\\' : Token('char','\\')}
        
        self.operatorSymbols = {'(' : Token('open', '('), ')' : Token('close', ')'), '-' : Token('dash', '-'), '+' : Token('plus', '+'), 
                                '*': Token('kleene', '*'), '.' : Token('dot', '.'), '|' : Token('pipe', '|')}

    def lex(self, expression):
        ts = TokenStream()
        for i, char in enumerate(expression):
            if i + 1 < len(expression):
                if expression[i] + expression[i+1] in self.escapedChars:
                    escChar = expression[i] + expression[i+1]
                    ts.addToken(self.escapedChars[escChar])
                    continue
            if char in self.operatorSymbols:
                ts.addToken(self.operatorSymbols[char])
            else:
                ts.addToken(Token('char', char))
        return ts

def main():
    if len(sys.argv) != 2:
        print("Check your input, should only include a single file after the program name")
    
    cfg = CFG()

    try:
        with open(sys.argv[1]) as file:
            for line in file:
                cfg.add_production_rule(line.strip())
    except FileNotFoundError:
        print(f"File '{sys.argv[1]}' not found, check your input")
    
    for lhs in cfg.productionRules:
        for rhs in cfg.productionRules[lhs]:
            print(lhs, "->", rhs, cfg.predict_set(lhs, rhs))
    cfg.generate_llt()
    l = Lexer()
    ts = l.lex('A-D.g+') # this is just a stand in for now lexer just takes in a string and coverts it to tokens
    tree = cfg.parse(ts)
    for child in tree.children:
        print(child.value)
    print(cfg)


if __name__ == "__main__":
    main()
