
import decimal
from decimal import Decimal
from math import sin, cos, tan, log, log10
import time
from typing import Iterator, List, Optional, Union, Tuple


FUNCTION_NAMES = ("sin", "cos", "tan", "cot", "ln", "log")

SUCCESS = 0
INVALID_EXPRESSION = 1
VALUE_ERROR = 2
ZERO_DIVISION_ERROR = 3
OVERFLOW_ERROR = 4
TIMEOUT_ERROR = 5
MEMORY_ERROR = 6


def print2(*args: type, sep: str = " ", end: str = "\n") -> None:
    """
    Like print, but only prints if unit tests aren't happening.
    
    arguments:
        args (type): The things to print.
        sep (str): What to print between arguments.
        end (str): What to print at the end.
    
    return:
        None
    """
    
    if print2.testing:
        return
    
    print(*args, sep=sep, end=end)

print2.testing = False


def check_timeout() -> None:
    """
    Raises TimeoutError if too much time has passed while evaluating an expression.
    
    return:
        None
    """
    
    start_time = check_timeout.start_time
    call_count = check_timeout.call_count = (check_timeout.call_count + 1) & 0b1111111111
    
    # only check after approximately every 1000 calls since getting the system time takes a while
    if call_count == 0 and (time.time() - start_time) > check_timeout.timeout:
        raise TimeoutError("expression took too long to evaluate")

check_timeout.start_time = 0.0 # set this in the calculate function
check_timeout.call_count = 0
check_timeout.timeout = 1.0


def cot(x: Union[int, Decimal]) -> Decimal:
    """
    Returns the cotangent of x radians.
    
    arguments:
        x (Union[int, Decimal]): The int or Decimal to get the cotangent of.
    
    return:
        Decimal: The result of cot(x).
    """
    
    return Decimal(1 / tan(x))


# this is used instead of just double asterisk operator since large exponentiation might take too long
def pure_python_exp(b: Union[int, Decimal], n: Union[int, Decimal]) -> Union[int, Decimal]:
    """
    Returns b raised to the power of n.
    
    arguments:
        base (Union[int, Decimal]): The base.
        exponent Union[int, Decimal]): The exponent to raise b to.
    
    return:
        Union[int, Decimal]: b raised to the power of n.
    """
    try:
        if n == 0:
            return b**n # return either 1 or 1.0
        
        exponent_is_int = isinstance(n, int)
        exponent_is_negative = (n < 0)
        if exponent_is_negative:
            n = -n
        current_value = b
        iteration_count = 1
        
        while iteration_count < n:
            check_timeout()
            
            current_value *= b
            iteration_count += 1
        
        if not exponent_is_int:
            n -= iteration_count
            current_value = Decimal(current_value)
            current_value *= (b**n)
        
        return current_value if not exponent_is_negative else (1 / Decimal(current_value))
    except decimal.InvalidOperation:
        raise OverflowError


def calculate(expression: str) -> Tuple[int, Union[int, Decimal]]:
    """
    Returns a tuple containing the return status and, if it could be evaluated, the value of the expression, otherwise 0.
    
    arguments:
        expression (str): The expression entered by the user.
    
    return:
        Tuple[int, Union[int, Decimal]]: The return status and, if it could be evaluated, the value of the expression, otherwise 0.
    """
    
    check_timeout.start_time = time.time()
    
    result = 0
    
    try:
        tokens = get_tokens(expression)
        
        if not tokens: # invalid token found, or nothing entered
            return (INVALID_EXPRESSION, 0)
        
        if not check_correctness(tokens):
            return (INVALID_EXPRESSION, 0)
        
        result = evaluate(tokens)
        
        if result is not None:
            print2("result:", result)
    except ValueError as e:
        print2("couldn't print result due to ValueError exception:", e)
        return (VALUE_ERROR, 0)
    except ZeroDivisionError as e:
        print2("couldn't print result due to ZeroDivisionError exception:", e)
        return (ZERO_DIVISION_ERROR, 0)
    except OverflowError as e:
        print2("couldn't print result due to OverflowError exception:", e)
        return (OVERFLOW_ERROR, 0)
    except TimeoutError as e:
        print2("couldn't print result due to TimeoutError exception:", e)
        return (TIMEOUT_ERROR, 0)
    except MemoryError as e:
        print2("couldn't print result due to MemoryError exception:", e)
        return (MEMORY_ERROR, 0)
    print2()
    
    return (SUCCESS, result)


def get_tokens(expression: str) -> List[Union[int, Decimal, str]]:
    """
    Converts an infix math expression string to a list of tokens.
    
    arguments:
        expression (str): The infix expression string.
    
    return:
        List[Union[int, Decimal, str]]: A list of tokens representing the infix expression, or an empty list if any token can't be evaluated.
    """
    
    expression = expression.replace(" ", "")
    
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
            print2("couldn't evaluate token:", token)
    
    return tokens


def get_next_token(iterator: Iterator[str], next_char: str = "") -> Tuple[Union[int, Decimal, str], bool, str]:
    """
    Gets the next token from the infix expression passed as an iterator.
    
    arguments:
        iterator (Iterator[str]): An iterator from the infix expression.
        next_char (str): The next character to check, or an empty string if the next character should be taken from the iterator.
    
    return:
        Tuple[Union[int, Decimal, str], bool, str]: A tuple containing the next token, a boolean indicating if the token was read successfully, and the next character to check, in that order.
    """
    
    next_char = next(iterator, "") if not next_char else next_char
    next_char_2 = ""
    next_char_3 = ""
    
    number_chars = []
    wrong_token = []
    dots_seen = 0
    
    if not next_char:
        return ("end", True, "") # got all tokens
    
    if next_char in "+-*/^(){}":
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
            
    elif next_char in "0123456789.":
        
        while next_char and next_char in "0123456789.":
            check_timeout()
            
            dots_seen += next_char == "."
            number_chars.append(next_char)
            next_char = next(iterator, "")
        
        number_string = "".join(number_chars)
        
        if dots_seen < 2 and number_string != ".":
            return (get_int_or_decimal_from_string(number_string), True, next_char)
        
        # invalid number
        return (number_string, False, "")
    
    wrong_token.extend((next_char, next_char_2, next_char_3))
    
    next_char = next(iterator, "")
    while next_char and next_char not in " 0123456789+-*/^(){}":
        check_timeout()
        
        wrong_token.append(next_char)
        next_char = next(iterator, "")
    
    return ("".join(wrong_token), False, "") # couldn't evaluate token


def get_int_or_decimal_from_string(number_string: str) -> Union[int, Decimal]:
    """
    Converts a string to an int or Decimal.
    
    arguments:
        number_string (str): A string representing an int or Decimal.
    
    return:
        Union[int, Decimal]: The number_string argument converted to an int or Decimal.
    """
    
    left_of_decimal = 0
    right_of_decimal = 0
    dot_seen = False
    divide_by = 1
    
    for char in number_string:
        check_timeout()
        
        if char == ".":
            dot_seen = True
        elif not dot_seen:
            left_of_decimal *= 10
            left_of_decimal += ord(char) - ord("0")
        else:
            right_of_decimal *= 10
            right_of_decimal += ord(char) - ord("0")
            divide_by *= 10
    
    if dot_seen:
        return Decimal(left_of_decimal) + (Decimal(right_of_decimal) / divide_by)
    
    return left_of_decimal


def check_correctness(tokens: List[Union[int, Decimal, str]]) -> bool:
    """
    Checks if the infix expression is written correctly.
    
    arguments:
        tokens (List[Union[int, Decimal, str]]): A list of tokens representing the infix expression.
    
    return:
        bool: True if the infix expression is written correctly, otherwise False.
    """
    
    if not check_parens_correctness(tokens):
        return False
    
    print2("checking the expression's tokens.")
    
    result = recursive_check_correctness(iter(tokens))
    
    print2() # recursive_check_correctness message doesn't end on a newline if successful
    
    return result


def check_parens_correctness(tokens: List[Union[int, Decimal, str]]) -> bool:
    """
    Checks if parentheses are included correctly. Checks for open parentheses, empty parentheses, and missing parentheses after functions.
    
    arguments:
        tokens (List[Union[int, Decimal, str]]): A list of tokens representing the infix expression.
    
    return:
        bool: True if the infix expression's parentheses are included correctly, otherwise False.
    """
    
    parens_stack = []
    
    for token in tokens:
        check_timeout()
        
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
            print2("invalid input: unmatched parentheses (open lefthand side)")
            return False
        
        del parens_stack[-1]
    
    if parens_stack:
        print2("invalid input: unmatched parentheses (open righthand side)")
        return False
    
    # prior part ensures there will always be a character after a ( or a {
    for next_idx, token in enumerate(tokens, 1):
        check_timeout()
        
        if token in FUNCTION_NAMES and next_idx < len(tokens) and tokens[next_idx] != "(":
            print2("invalid input: expected \"(\" after", token)
            return False
        elif token == "(" and tokens[next_idx] == ")":
            print2("invalid input: empty () parens")
            return False
        elif token == "{" and tokens[next_idx] == "}":
            print2("invalid input: empty {} parens")
            return False
        
    return True


def recursive_check_correctness(iter_tokens: Iterator[Union[int, Decimal, str]]) -> bool:
    """
    Recursively checks if an infix expression and its parenthesized expressions are written correctly.
    
    arguments:
        iter_tokens (Iterator[Union[int, Decimal, str]]): An iterator of tokens representing the infix expression.
    
    return:
        bool: True if the infix expression and its parenthesized expressions are written correcly, otherwise False.
    """
    
    operator_expected = False
    
    for token in iter_tokens:
        check_timeout()
        
        print2(token, end=" ")
        
        if token in ("(", "{"):
            if not recursive_check_correctness(iter_tokens):
                return False
            operator_expected = True
        elif token in (")", "}"):
            break
        elif operator_expected and token not in ("+", "-", "*", "/", "^"):
            print2("\ninvalid input: didn't see operator when one was expected", token)
            return False
        elif not operator_expected and token in ("*", "/", "^"): # + and - allowed as unary operators
            print2("\ninvalid input: saw unexpected operator")
            return False
        elif not isinstance(token, str): # it's a number
            operator_expected = True
        elif token in ("+", "-", "*", "/", "^"):
            operator_expected = False
    
    if not operator_expected:
        print2("\ninvalid input: whole expression or parenthesized expression ended with an operator")
        return False
    
    return True


def evaluate(tokens: List[Union[int, Decimal, str]]) -> Optional[Union[int, Decimal]]:
    """
    Evaluates an infix expression.
    
    arguments:
        tokens (List[Union[int, Decimal, str]]): A list of tokens representing the infix expression.
    
    return:
        Optional[Union[int, Decimal]]: The result of the infix expression, or None if it couldn't be evaluated (e.g. division by zero).
    """
    
    easier_tokens = nest_parenthesized_expressions(iter(tokens))
    
    easier_tokens = nest_functions(iter(easier_tokens))
    
    # do this here since ^ has higher precenence than unaries
    # do it in reverse because a^b^c is equal to (a^(b^c)), not ((a^b)^c)
    easier_tokens = nest_exponentiation(reversed(easier_tokens))
    
    easier_tokens = convert_to_no_unaries(iter(easier_tokens))
    
    return shunting_yard_evaluation(iter(easier_tokens))


def nest_parenthesized_expressions(iter_tokens: Iterator[Union[int, Decimal, str]]) -> List[Union[int, Decimal, str, list]]:
    """
    Simplifies the token list by getting rid of parentheses and instead recursively putting parenthesized expressions in nested lists.
    
    arguments:
        iter_tokens (Iterator[Union[int, Decimal, str]]): An iterator of tokens representing the infix expression.
    
    return:
        List[Union[int, Decimal, str, list]]: A new token list where the parenthesized expressions are recursively placed in nested lists.
    """
    
    easier_tokens = []
    
    for token in iter_tokens:
        check_timeout()
        
        if token in (")", "}"):
            return easier_tokens
        elif token in ("(", "{"):
            easier_tokens.append(nest_parenthesized_expressions(iter_tokens))
        else:
            easier_tokens.append(token)
    
    return easier_tokens


def nest_functions(iter_tokens: Iterator[Union[int, Decimal, str]]) -> List[Union[int, Decimal, str, list]]:
    """
    Places instances of functions in nested lists. This is done to isolate the return value better. It makes nesting exponentiation easier.
    
    arguments:
        iter_easier_tokens (Iterator[Union[int, Decimal, str, list]]): An iterator of tokens representing the infix expression.
    
    return:
        List[Union[int, Decimal, str, list]]: A new token list where instances of exponentiation are placed in nested lists.
    """
    
    easier_tokens = []
    
    for token in iter_tokens:
        check_timeout()
        
        if isinstance(token, list):
            easier_tokens.append(nest_functions(iter(token)))
        elif token in FUNCTION_NAMES:
            easier_tokens.append([token, nest_functions(iter(next(iter_tokens)))])
        else:
            easier_tokens.append(token)
    
    return easier_tokens


def nest_exponentiation(iter_easier_tokens: Iterator[Union[int, Decimal, str, list]]) -> List[Union[int, Decimal, str, list]]:
    """
    Places instances of exponentiation in nested lists. This is done to prepare for unary operator removal since exponentiation has higher precedence.
    
    arguments:
        iter_easier_tokens (Iterator[Union[int, Decimal, str, list]]): An iterator of tokens representing the infix expression.
    
    return:
        List[Union[int, Decimal, str, list]]: A new token list where instances of exponentiation are placed in nested lists.
    """
    
    easier_tokens = []
    
    for token in iter_easier_tokens:
        check_timeout()
        
        if isinstance(token, list):
            easier_tokens.append(nest_exponentiation(reversed(token)))
        elif token != "^":
            easier_tokens.append(token)
        else:
            base_token = next(iter_easier_tokens)
            if isinstance(base_token, list):
                base_token = nest_exponentiation(reversed(base_token))
            nested_exponentiation = [base_token, token] # b^
            
            # adding exponent and any unary operators
            previously_added_token = easier_tokens.pop()
            while previously_added_token == "+" or previously_added_token == "-":
                check_timeout()
                
                nested_exponentiation.append(previously_added_token)
                previously_added_token = easier_tokens.pop()
            nested_exponentiation.append(previously_added_token)
            
            easier_tokens.append(nested_exponentiation)
    
    easier_tokens.reverse()
    
    return easier_tokens


def convert_to_no_unaries(iter_easier_tokens: Iterator[Union[int, Decimal, str, list]]) -> List[Union[int, Decimal, str, list]]:
    """
    Returns A list of tokens representing an equivalent infix expression without unary tokens by instead multiplying values by -1.
    
    arguments:
        iter_easier_tokens (Iterator[Union[int, Decimal, str, list]]): An iterator of tokens representing the infix expression.
    
    return:
        List[Union[int, Decimal, str, list]]: A list of tokens representing an equivalent infix expression without unary tokens.
    """
    
    easier_tokens = []
    
    minuses_in_a_row = 0
    
    for token in iter_easier_tokens:
        check_timeout()
        
        if token == "+":
            continue
        elif token == "-":
            minuses_in_a_row += 1
        else:
            if minuses_in_a_row % 2 == 1:
                
                easier_tokens.append([-1, "*", token])
                if token in FUNCTION_NAMES:
                    token = convert_to_no_unaries(iter(next(iter_easier_tokens)))
                    easier_tokens[-1].append(token)
                elif isinstance(token, list):
                    easier_tokens[-1][-1] = convert_to_no_unaries(iter(token))
            else:
                
                if token in FUNCTION_NAMES:
                    easier_tokens.append(token)
                    token = convert_to_no_unaries(iter(next(iter_easier_tokens)))
                    easier_tokens.append(token)
                elif isinstance(token, list):
                    easier_tokens.append(convert_to_no_unaries(iter(token)))
                else:
                    easier_tokens.append(token)
            
            # adding next operator
            token = next(iter_easier_tokens, None)
            if token is not None:
                easier_tokens.append(token)
            
            minuses_in_a_row = 0
    
    return easier_tokens


# https://en.wikipedia.org/wiki/Shunting_yard_algorithm
def shunting_yard_evaluation(iter_easier_tokens: Iterator[Union[int, Decimal, str, list]]) -> Optional[Union[int, Decimal]]:
    """
    Evaluates an infix expression using Shunting yard algorithm.
    
    arguments:
        iter_easier_tokens (Iterator[Union[int, Decimal, str, list]]): An iterator of tokens representing the infix expression.
    
    return:
        Optional[Union[int, Decimal]]: The result of the infix expression, or None if it couldn't be evaluated (e.g. division by zero).
    """
    
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
    
    inner_expression_result = None
    argument = None
    function = None
    operator = None
    
    for token in iter_easier_tokens:
        check_timeout()
        
        token_is_list = isinstance(token, list)
        
        # avoids trying to hash a list
        if not token_is_list:
            function = function_mapping.get(token)
            operator = precedence.get(token)
            
        if token_is_list:
            
            inner_expression_result = shunting_yard_evaluation(iter(token))
            output_queue.append(inner_expression_result)
            if inner_expression_result is None:
                return None
            
        elif not isinstance(token, str): # it's a number
            output_queue.append(token)
        elif function is not None:
            
            argument = shunting_yard_evaluation(iter(next(iter_easier_tokens)))
            if argument is None:
                return None
            try:
                output_queue.append(Decimal(function(argument)))
            except (ValueError, ZeroDivisionError) as e:
                if token == "cot" or token == "tan":
                    print2(token, "(", argument, ") is undefined", sep="")
                else: # ln or log
                    print2(token, "(", argument, ") isn't a real number", sep="")
                raise e
            
        elif operator is not None:
            
            while operator_stack and precedence[token] <= precedence[operator_stack[-1]]:
                check_timeout()
                
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
            
    
    while operator_stack:
        check_timeout()
        
        output_queue.append(operator_stack.pop())
    
    try:
        return rpn_evaluation(output_queue)
    except ZeroDivisionError as e:
        print2("couldn't evaluate expression due to ZeroDivisionError exception:", e)
        raise e


# https://www.geeksforgeeks.org/evaluate-the-value-of-an-arithmetic-expression-in-reverse-polish-notation-in-java/
def rpn_evaluation(output_queue: List[Union[int, Decimal, str]]) -> Union[int, Decimal]:
    """
    Evaluates a reverse Polish notation expression.
    
    arguments:
        List[Union[int, Decimal, str]]: A list of tokens in reverse Polish notation order.
    
    return:
        Union[int, Decimal]: The result of the reverse Polish notation expression.
    """
    
    evaluation_stack = []
    
    operators = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: Decimal(x / y),
        "^": lambda x, y: pure_python_exp(x, y)
    }
    
    operator = None
    operand1 = None
    operand2 = None
    
    for token in output_queue:
        check_timeout()
        
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


def main() -> int:
    """
    The main function.
    
    return:
        int: The exit status.
    """
    
    prompt = "enter an infix math expression, or \"quit\" to quit: "
    
    expression = ""
    tokens = []
    
    while True:
        
        tokens.clear()
        
        try:
            expression = input(prompt).strip().lower()
            
            if expression == "quit":
                break
            
            calculate(expression)
        except SyntaxError as e:
            print("couldn't evaluate expression due to unexpected error:", e)
        
    print("\ngoodbye")
    
    return 0


if __name__ == "__main__":
    main()
