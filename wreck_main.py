from LL1parser import CFG, Lexer
from nfagen import NFA
import sys 

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
    
    # for lhs in cfg.productionRules:
    #     for rhs in cfg.productionRules[lhs]:
    #         print(lhs, "->", rhs, cfg.predict_set(lhs, rhs))
    
    # ---------------- PARSING AND SDT -------------------#
    cfg.generate_llt()
    l = Lexer()
    ts = l.lex('A-D.g+') # this is just a stand in for now lexer just takes in a string and coverts it to tokens
    tree = cfg.parse(ts)

    # --------------- NFA GENERATION ----------------------#
    alphabet = ["a", "b", "c"]
    nfa = NFA(alphabet)
    nfa.lambda_wrap(0, 1, tree)
    print(nfa.T)
    print(nfa.L)
    print(nfa)


if __name__ == "__main__":
    main()
