###########################
# CONSTANTS
###########################
DIGITS = '0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'

#################################
# TOKEN TYPES
#################################
TT_INT        = 'INT'
TT_FLOAT      = 'FLOAT'
TT_PLUS       = 'PLUS'
TT_MINUS      = 'MINUS'
TT_MUL        = 'MUL'
TT_DIV        = 'DIV'
TT_LPAREN     = 'LPAREN'
TT_RPAREN     = 'RPAREN'
TT_EQ         = 'EQ'
TT_IDENTIFIER = 'IDENTIFIER'

#################################
# TOKEN CLASS
#################################
class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f'{self.type}:{self.value}'
        return f'{self.type}'

#################################
# ERROR CLASSES
#################################
class Error:
    def __init__(self, pos, details):
        self.pos = pos
        self.details = details

    def __str__(self):
        return self.as_string()

    def as_string(self):
        return f'Error at position {self.pos}: {self.details}'

class IllegalCharError(Error):
    def __init__(self, pos, char):
        super().__init__(pos, f"Illegal character '{char}'")

#################################
# LEXER
#################################
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = -1
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == '=':
                tokens.append(Token(TT_EQ))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.advance()
            else:
                pos = self.pos
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos, char)

        return tokens, None

    def make_identifier(self):
        id_str = ''
        while self.current_char is not None and self.current_char in LETTERS + DIGITS:
            id_str += self.current_char
            self.advance()
        return Token(TT_IDENTIFIER, id_str)

    def make_number(self):
        num_str = ''
        dot_count = 0

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))

#################################
# AST NODES
#################################
class NumberNode:
    def __init__(self, tok):
        self.tok = tok

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

#################################
# PARSER
#################################
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        self.current_tok = self.tokens[self.tok_idx] if self.tok_idx < len(self.tokens) else None
        return self.current_tok

    def parse(self):
        if self.current_tok is None:
            return None
        result = self.statement()
        return result

    def statement(self):
        if self.current_tok.type == TT_IDENTIFIER:
            var_name = self.current_tok
            self.advance()
            if self.current_tok is not None and self.current_tok.type == TT_EQ:
                self.advance()
                expr = self.expr()
                return VarAssignNode(var_name, expr)
        return self.expr()

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def factor(self):
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(tok)
        elif tok.type == TT_IDENTIFIER:
            self.advance()
            return VarAccessNode(tok)
        elif tok.type == TT_LPAREN:
            self.advance()
            expr = self.expr()
            if self.current_tok is not None and self.current_tok.type == TT_RPAREN:
                self.advance()
                return expr
            else:
                raise Exception("Expected ')'")
        else:
            raise Exception(f"Unexpected token: {tok}")

    def bin_op(self, func, ops):
        left = func()

        while self.current_tok is not None and self.current_tok.type in ops:
            op_tok = self.current_tok
            self.advance()
            right = func()
            left = BinOpNode(left, op_tok, right)

        return left

#################################
# PARSE TREE PRINTER
#################################
def print_tree(node, indent='', last=True):
    marker = '└── ' if last else '├── '

    if isinstance(node, NumberNode):
        print(indent + marker + f'Number({node.tok.value})')

    elif isinstance(node, VarAccessNode):
        print(indent + marker + f'Var({node.var_name_tok.value})')

    elif isinstance(node, VarAssignNode):
        print(indent + marker + '=')
        indent += '    ' if last else '│   '
        print_tree(VarAccessNode(node.var_name_tok), indent, False)
        print_tree(node.value_node, indent, True)

    elif isinstance(node, BinOpNode):
        print(indent + marker + f'{node.op_tok.value}')
        indent += '    ' if last else '│   '
        print_tree(node.left_node, indent, False)
        print_tree(node.right_node, indent, True)

#################################
# RUN FUNCTION
#################################
def run(text):
    lexer = Lexer(text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    parser = Parser(tokens)
    ast = parser.parse()
    return ast, None

#################################
# MAIN LOOP (REPL)
#################################
if __name__ == "__main__":
    while True:
        text = input("basic> ")
        if text.strip().lower() in ['exit', 'quit']:
            break
        result, error = run(text)
        if error:
            print(error.as_string())
        else:
            print("Parse Tree:")
            print_tree(result)
