import sys
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
        self.delete_all_children()
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
        newKids = replacement.children
        self.delete_all_children()
        self.adopt_children(newKids)
        self.kind = replacement.kind
        self.value = replacement.value
    
    def copy(self):
        processed = set()
        newNode = self.copy_children(processed)
        return newNode
    
    def copy_children(self, processed):
        processed.add(self)
        newNode = Node(kind=self.kind, val=self.value)
        newNode.parent = self.parent
        newKids = []
        for child in self.children:
            if child not in processed:
                newChild = child.copy_children(processed)
                newKids.append(newChild)
        newNode.adopt_children(newKids)
        return newNode
        
    def adopt_children(self, newChildren):
        for child in newChildren:
            child.parent = self
            self.children.append(child)

    def remove_child(self, child):
        self.children.remove(child)
    
    def delete_all_children(self):
        for c in self.children:
            c.parent = None
        self.children.clear()

    def SEMANTIC_ERROR(self, error_specifics=None):
        error_message = 'SemanticError' 
        if error_specifics is not None:
            error_message += ': ' + error_specifics
        print(error_message)
        sys.exit(3)

    def NUCLEUS(self):
        if self.children[0].kind == 'open':
            altNode = self.children[1]
            self.replace_self(altNode)
            return self
        if self.has_child_of_kind('CHARRNG'):
            charrngChild = self.get_child_of_kind('CHARRNG')
            if charrngChild.has_child_of_kind('char'):
                leftChar = self.get_child_of_kind('char')
                rightChar = charrngChild.get_child_of_kind('char')
                rangeNode = Node(kind='range')
                if ord(leftChar.value) > ord(rightChar.value):
                    self.SEMANTIC_ERROR('invalid char range')
                else:
                    rangeNode.add_child(leftChar)
                    rangeNode.add_child(rightChar)
                    self.replace_self(rangeNode)
                return self
            if charrngChild.has_child_of_kind('\u03BB'):
                self.remove_child(charrngChild)
                replacement = self.children[0]
                self.replace_self(replacement)
                return self
        if self.has_child_of_kind('dot'):
            dotChild = self.get_child_of_kind('dot')
            self.replace_self(dotChild)
            return self
        return self
    
    def ATOM(self):
        if self.has_child_of_kind('ATOMMOD'):
            child = self.get_child_of_kind('ATOMMOD')
            if child.has_child_of_kind('\u03BB'):
                leftChild = self.children[0]
                replacement = leftChild
                self.replace_self(replacement)
                return self
            if child.has_child_of_kind('kleene'):
                newAtom = Node(kind='kleene')
                newAtom.add_child(self.children[0]) # leftmost child
                self.replace_self(newAtom)
                return self
            if child.has_child_of_kind('plus'):
                newAtom = Node(kind='SEQLIST')
                newAtom.add_child(self.children[0]) 
                newKleen = Node(kind='kleene')
                newKleen.add_child(self.children[0].copy())
                newAtom.add_child(newKleen)
                self.replace_self(newAtom)
                return self
        return self

    def SEQLIST(self):
        parent = self.parent
        if self.has_child_of_kind('\u03BB'):
            parent.remove_child(self)
            return self
        if parent.kind == 'SEQLIST':
            grandkids = self.children
            parent.remove_child(self)
            parent.adopt_children(grandkids)
            return self        
        return self

    def SEQ(self):
        while self.has_child_of_kind('SEQLIST'):
            child = self.get_child_of_kind('SEQLIST')
            grandKids = child.children
            self.remove_child(child)
            self.adopt_children(grandKids)
        if len(self.children) == 1:
            replacement = self.children[0]
            self.replace_self(replacement)
        return self

    def ALTLIST(self):
        parent = self.parent
        if len(self.children) == 1 and self.has_child_of_kind('\u03BB'):
            parent.remove_child(self)
            return self
        if parent.kind == 'ALTLIST':
            grandkids = self.children
            parent.adopt_children(grandkids)
            return self
        return self
    
    def ALT(self):
        while self.has_child_of_kind('ALTLIST'):
            child = self.get_child_of_kind('ALTLIST')
            grandchildren = child.children
            self.remove_child(child)
            self.adopt_children(grandchildren)
        for c in self.children:
            if c.kind == 'pipe':
                self.remove_child(c)
        if len(self.children) == 1:
            replacement = self.children[0]
            self.replace_self(replacement)
        return self

    def RE(self):
        return self.children[0]
    
    def sdt_procedure(self):
        if self.kind == 'NUCLEUS':
            return(self.NUCLEUS())
        if self.kind == 'ATOM':
            return(self.ATOM())
        if self.kind == 'SEQ':
            return(self.SEQ())
        if self.kind == 'SEQLIST':
            return(self.SEQLIST())
        if self.kind == 'ALT':
            return(self.ALT())
        if self.kind == 'ALTLIST':
            return(self.ALTLIST())
        if self.kind == 'RE':
            return(self.RE())
        return self
    
    def __repr__(self):
        chillins = [c.kind for c in self.children]
        printStr = f'self:({self.kind}, {self.value}) --> children:{chillins}'
        return printStr