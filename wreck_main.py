from LL1parser import CFG, Lexer
from nfagen import NFA
import sys 

def main():
    if len(sys.argv) != 2:
        print("Check your input, should only include a single file after the program name")
    lexConfigFile = sys.argv[1]
    cfg = CFG()
    cfgFile = 'llre.cfg'
    try:
        with open(cfgFile) as file:
            for line in file:
                cfg.add_production_rule(line.strip())
    except FileNotFoundError:
        print(f"File '{sys.argv[1]}' not found, check your input")
    
    # for lhs in cfg.productionRules:
    #     for rhs in cfg.productionRules[lhs]:
    #         print(lhs, "->", rhs, cfg.predict_set(lhs, rhs))
    
    # ---------------- PARSING AND SDT -------------------#
    cfg.generate_llt()
    try:
        with open(lexConfigFile) as file:
            fileData = file.readlines()
    except FileNotFoundError:
        print(f"File '{sys.argv[1]}' not found, check your input")
    
    alphabet = [char for char in fileData[0]]
    for line in fileData:
        regEx, tokenId, tokenValue = line[0].split()
        l = Lexer()
        ts = l.lex(regEx)
        tree = cfg.parse(ts)

    # --------------- NFA GENERATION ----------------------#
    # alphabet = ["a", "b", "c"]
    nfa = NFA(alphabet)
    nfa.lambda_wrap(0, 1, tree)
    print(nfa.T)
    print(nfa.L)
    print(nfa)


if __name__ == "__main__":
    main()
