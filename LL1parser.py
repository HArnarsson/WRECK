#!/usr/bin/env python3

import sys
from collections import namedtuple
# from nfagen import NFA
from node import Node
# lambda_symbol = '\u03BB'

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
            elif x in self.terminals or x == '\u03BB':
                if x in self.terminals:
                    if x != ts.peek():
                        print(f"Value between token stream and expected value don't match. val:{x}, ts:{ts.peek()}, exiting...")
                        sys.exit(2)
                    x, value = ts.pop()
                else: value = 'lambda'   
                current.add_child(Node(kind=x, val=value))
            elif x == "*":
                current = current.sdt_procedure()
                current = current.parent
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
        if self.tokens: 
            t = self.tokens.pop(0)
            return t.type, t.value
        else: return '$', '$'

    def __str__(self):
        printStr = ''
        for token in self.tokens:
            printStr += token.type + ' ' + token.value + '\n'
        return printStr

class Lexer():
    def __init__(self):
        self.escapedChars = {'\|' : Token('char', '|'), '\*' : Token('char', '*'), '\+' : Token('char', '+'), '\.' : Token('char', '.'), 
                             '\(' : Token('char', '('), '\)' : Token('char', ')'), '\-' : Token('char', '-'), '\s' : Token('char', 'x20'), 
                             '\n' : Token('char', 'x0a'), '\\' : Token('char','\\')}
        
        self.operatorSymbols = {'(' : Token('open', '('), ')' : Token('close', ')'), '-' : Token('dash', '-'), '+' : Token('plus', '+'), 
                                '*': Token('kleene', '*'), '.' : Token('dot', '.'), '|' : Token('pipe', '|')}

    def lex(self, expression):
        ts = TokenStream()
        i = 0
        while i < len(expression):
            char = expression[i]
            if i + 1 < len(expression):
                if expression[i] + expression[i+1] in self.escapedChars:
                    escChar = expression[i] + expression[i+1]
                    ts.addToken(self.escapedChars[escChar])
                    i += 2
                    continue
            if char in self.operatorSymbols:
                ts.addToken(self.operatorSymbols[char])
            else:
                ts.addToken(Token('char', char))
            i += 1
        # print(ts)
        return ts

