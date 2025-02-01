

from math import sin, cos, tan, log, log10


FUNCTION_NAMES = ("sin", "cos", "tan", "cot", "ln", "log")


def cot(x):
    
    return 1 / tan(x)


def get_tokens(expression):
    
    tokens = []
    next_char = ""
    
    # ignore equals sign at the end, if there is one
    if expression and expression[-1] == "=":
        expression = expression[:-1]
    
    if expression:
        iterator = iter(expression)
        
        token, read_successfully, next_char = get_next_token(iterator, next_char)
        while token != "end" and read_successfully:
            tokens.append(token)
            token, read_successfully, next_char = get_next_token(iterator, next_char)
        
        # token.strip() != "=" is checked so users can optionally enter = at the end
        if not read_successfully:
            tokens.clear()
            print("couldn't evaluate token:", token)
    
    return tokens


def get_next_token(iterator, next_char=""):
    
    next_char = next(iterator, "") if not next_char else next_char
    next_char_2 = ""
    next_char_3 = ""
    
    number_chars = []
    wrong_token = []
    dots_seen = 0
    
    # ignore space characters
    while next_char == " ":
        next_char = next(iterator, "")
    
    if not next_char:
        return ("end", True, "") # got all tokens
    
    if next_char and next_char in "+-*/^(){}":
        return (next_char, True, "")
    elif next_char == "s":
        
        next_char_2 = next(iterator, "")
        next_char_3 = next(iterator, "")
        if next_char_2 == "i" and next_char_3 == "n":
            return ("sin", True, "")
        
    elif next_char == "t":
        
        next_char_2 = next(iterator, "")
        next_char_3 = next(iterator, "")
        if next_char_2 == "a" and next_char_3 == "n":
            return ("tan", True, "")
        
    elif next_char == "c":
        
        next_char_2 = next(iterator, "")
        next_char_3 = next(iterator, "")
        if next_char_2 == "o":
            if next_char_3 == "s":
                return ("cos", True, "")
            elif next_char_3 == "t":
                return ("cot", True, "")
            
    elif next_char == "l":
        
        next_char_2 = next(iterator, "")
        if next_char_2 == "n":
            return ("ln", True, "")
        elif next_char_2 == "o":
            next_char_3 = next(iterator, "")
            if next_char_3 == "g":
                return ("log", True, "")
            
    elif next_char and next_char in "0123456789.":
        
        while next_char and next_char in "0123456789.":
            dots_seen += next_char == "."
            number_chars.append(next_char)
            next_char = next(iterator, "")
        
        number_string = "".join(number_chars)
        
        if dots_seen < 2 and number_string != ".":
            return (get_int_or_float_from_string(number_string), True, next_char)
        
        # invalid number
        return (number_string, False, "")
    
    wrong_token.extend((next_char, next_char_2, next_char_3))
    
    next_char = next(iterator, "")
    while next_char and next_char != " " and next_char not in " 0123456789+-*/^(){}":
        wrong_token.append(next_char)
        next_char = next(iterator, "")
    
    return ("".join(wrong_token), False, "") # couldn't evaluate token


def get_int_or_float_from_string(number_string):
    
    left_of_decimal = 0
    right_of_decimal = 0
    dot_seen = False
    divide_by = 1
    
    for char in number_string:
        if char == ".":
            dot_seen = True
        elif not dot_seen:
            left_of_decimal *= 10
            left_of_decimal += ord(char) - ord("0")
        else:
            right_of_decimal *= 10
            right_of_decimal += ord(char) - ord("0")
            divide_by *= 10
    
    right_of_decimal /= divide_by
    
    return left_of_decimal if not dot_seen else left_of_decimal + right_of_decimal


def check_correctness(tokens):
    
    if not check_parens_correctness(tokens):
        return False
    
    print("checking expression tokens.")
    
    result = recursive_check_correctness(iter(tokens))
    
    print() # recursive_check_correctness message doesn't end on a newline if successful
    
    return result


def check_parens_correctness(tokens):
    
    parens_stack = []
    
    for token in tokens:
        if token not in ("(", ")", "{", "}"):
            continue
        
        if token in ("(", "{"):
            parens_stack.append(token)
            continue
        
        if (
            not parens_stack
            or (token == ")" and parens_stack[-1] != "(")
            or (token == "}" and parens_stack[-1] != "{")
            ):
            print("invalid input: unmatched parentheses (open lefthand side)")
            return False
        
        del parens_stack[-1]
    
    if parens_stack:
        print("invalid input: unmatched parentheses (open righthand side)")
        return False
    
    # prior part ensures there will always be a character after a ( or a {
    for next_idx, token in enumerate(tokens, 1):
        if token in FUNCTION_NAMES and next_idx < len(tokens) and tokens[next_idx] != "(":
            print("invalid input: expected \"(\" after", token)
            return False
        elif token == "(" and tokens[next_idx] == ")":
            print("invalid input: empty () parens")
            return False
        elif token == "{" and tokens[next_idx] == "}":
            print("invalid input: empty {} parens")
            return False
        
    return True


def recursive_check_correctness(iter_tokens):
    
    operator_expected = False
    
    for token in iter_tokens:
        print(token, end=" ")
        
        if token in ("(", "{"):
            if not recursive_check_correctness(iter_tokens):
                return False
            operator_expected = True
        elif token in (")", "}"):
            break
        elif operator_expected and token not in ("+", "-", "*", "/", "^"):
            print("\ninvalid input: didn't see operator when one was expected", token)
            return False
        elif not operator_expected and token in ("*", "/", "^"): # + and - allowed as unary operators
            print("\ninvalid input: saw unexpected operator")
            return False
        elif not isinstance(token, str): # it's an int or float
            operator_expected = True
        elif token in ("+", "-", "*", "/", "^"):
            operator_expected = False
    
    if not operator_expected:
        print("\ninvalid input: whole expression or parenthesized expression ended with an operator")
        return False
    
    return True


def evaluate(tokens):
    
    easier_tokens = nest_parenthesized_expressions(iter(tokens))
    easier_tokens = convert_to_no_unaries(iter(easier_tokens))
    
    return shunting_yard_evaluation(iter(easier_tokens))


def nest_parenthesized_expressions(iter_tokens):
    
    easier_tokens = []
    
    for token in iter_tokens:
        if token in (")", "}"):
            return easier_tokens
        elif token in ("(", "{"):
            easier_tokens.append(nest_parenthesized_expressions(iter_tokens))
        else:
            easier_tokens.append(token)
    
    return easier_tokens


def convert_to_no_unaries(iter_easier_tokens):
    
    easier_tokens = []
    
    unary_minuses_in_a_row = 0
    
    for token in iter_easier_tokens:
        if token == "+":
            continue
        elif token == "-":
            unary_minuses_in_a_row += 1
        else:
            if unary_minuses_in_a_row % 2 == 1:
                easier_tokens.append([-1, "*", token])
                if token in FUNCTION_NAMES:
                    easier_tokens[-1].append(next(iter_easier_tokens))
            else:
                easier_tokens.append(token)
            token = next(iter_easier_tokens, "")
            if token:
                easier_tokens.append(token)
            unary_minuses_in_a_row = 0
            
            if isinstance(easier_tokens[-1], list):
                easier_tokens[-1] = convert_to_no_unaries(iter(easier_tokens[-1]))
    
    return easier_tokens


def shunting_yard_evaluation(iter_easier_tokens):
    
    function_mapping = {
        "sin": sin,
        "cos": cos,
        "tan": tan,
        "cot": cot,
        "ln": log,
        "log": log10
    }
    
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    
    operator_stack = []
    output_queue = []
    
    function = None
    operator = None
    
    for token in iter_easier_tokens:
        token_is_list = isinstance(token, list)
        
        # avoids trying to hash a list
        if not token_is_list:
            function = function_mapping.get(token)
            operator = precedence.get(token)
        
        if token_is_list:
            output_queue.append(shunting_yard_evaluation(iter(token)))
        elif not isinstance(token, str): # it's an int or float
            output_queue.append(token)
        elif function is not None:
            output_queue.append(function(shunting_yard_evaluation(iter(next(iter_easier_tokens)))))
        elif operator is not None:
            while operator_stack and precedence[token] <= precedence[operator_stack[-1]]:
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
    
    while operator_stack:
        output_queue.append(operator_stack.pop())
    
    return rpn_evaluation(output_queue)


def rpn_evaluation(output_queue):
    
    evaluation_stack = []
    
    operators = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y,
        "^": lambda x, y: x**y
    }
    
    operator = None
    operand1 = None
    operand2 = None
    
    for token in output_queue:
        token_is_list = isinstance(token, list)
        
        # avoids trying to hash a list
        if not token_is_list:
            operator = operators.get(token)
        
        if operator is None:
            evaluation_stack.append(token)
        else:
            operand2 = evaluation_stack.pop()
            operand1 = evaluation_stack.pop()
            
            if isinstance(operand1, list):
                operand1 = rpn_evaluation(operand1)
            if isinstance(operand2, list):
                operand2 = rpn_evaluation(operand2)
            
            evaluation_stack.append(operator(operand1, operand2))
    
    return evaluation_stack[0]


def main():
    
    prompt = "enter an infix math expression, or \"quit\" to quit: "
    
    expression = ""
    tokens = []
    
    while True:
        
        tokens.clear()
        
        expression = input(prompt).strip()
        
        if expression == "quit":
            break
        
        tokens = get_tokens(expression)
        
        if not tokens: # invalid token found, or nothing entered
            continue
        
        if not check_correctness(tokens):
            continue
        
        print("the expression equals", evaluate(tokens), end="\n\n")
    
    print("goodbye")


if __name__ == "__main__":
    main()
