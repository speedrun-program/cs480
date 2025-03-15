
import os
from decimal import Decimal
from math import sin, cos, tan, log, log10
from random import randrange, seed
from typing import Dict, List, Union, Tuple

import cs480lab5main
from cs480lab5main import cot


CFG_FILE_DEFAULT_TEXT = """random seed:                     0                 (the random seed value)
max subexpression values:        5                 (how many numbers, functions, or subexpressions per expression or subexpression)
max subexpression depth:         5                 (how many levels of subexpressions there can be)
max consecutive unaries:         5                 (how many unary operators can appear in a row)
max digits in an int:            3                 (how many digits an int can have)
max lefthand digits in a float:  3                 (how many digits can be to the left of the dot in a float)
max righthand digits in a float: 3                 (how many digits can be to the right of the dot in a float)
max allowed error:               0.00000001        (largest absolute difference from expected result before the test is considered an error)
timeout:                         0.01              (max time a function can take to evaluate before timeout occurs)
tests:                           1000              (how many tests without errors should be ran)
random error chance:             50                (how often to add an error, e.g. if this is 50 then add an error to 1 in 50 tests)"""


# this function is used so the expression for eval doesn't need to work with Decimal objects
def cot2(x: Union[int, float]) -> float:
    """
    Returns the cotangent of x radians as a float. This function is for eval so it doesn't need to work with Decimal objects.
    
    arguments:
        x (Union[int, Decimal]): The int or Decimal to get the cotangent of.
    
    return:
        Decimal: The result of cot(x).
    """
    
    return 1 / tan(x)


def run_tests(cfg_settings: Dict[str, Union[int, Decimal]]) -> Tuple[
        List[Tuple[str, Union[int, Decimal, str], Union[int, Decimal, str]]],
        List[Tuple[str, Union[int, Decimal, str], Union[int, Decimal, str]]]
    ]:
    """
    Runs tests comparing cs480lab5main.calculate's results with evals results.
    
    arguments:
        cfg_settings (Dict[str, Union[int, Decimal]]): Configuration settings to control how the expression is created.
    
    return:
        Tuple[
            List[Tuple[str, Union[int, Decimal, str], Union[int, Decimal, str]]],
            List[Tuple[str, Union[int, Decimal, str], Union[int, Decimal, str]]]
        ]: The lists of successful tests and failed tests, which contain tuples of (expression, calculated result, expected result).
    """
    
    # these lists contain tuples with (expression, calculated result, expected result)
    success_list = []
    failure_list = []
    
    # NOTE: for these tests, VALUE_ERROR (e.g. passing -1 to ln) and ZERO_DIVISION_ERROR aren't considered errors
    for _ in range(cfg_settings["tests"]):
        
        error_this_test = (randrange(cfg_settings["random error chance"]) == 0)
        
        # insert an expression error if all the non error tests are done
        expression_token_strings = get_random_expression(cfg_settings)
        
        if error_this_test:
            add_an_error(expression_token_strings)
        
        expression = "".join(expression_token_strings)
        
        cs480lab5main_error, cs480lab5main_result = cs480lab5main.calculate(expression)
        
        if cs480lab5main_error == cs480lab5main.INVALID_EXPRESSION:
            cs480lab5main_result = "INVALID_EXPRESSION"
        
        # if it's OVERFLOW_ERROR, TIMEOUT_ERROR, or MEMORY_ERROR, consider it successful
        elif cs480lab5main_error == cs480lab5main.VALUE_ERROR or cs480lab5main_error == cs480lab5main.ZERO_DIVISION_ERROR:
            cs480lab5main_result = "EVALUATION_ERROR"
        elif cs480lab5main_error == cs480lab5main.OVERFLOW_ERROR:
            success_list.append((expression, "OVERFLOW_ERROR", "OVERFLOW_ERROR"))
            continue
        elif cs480lab5main_error == cs480lab5main.TIMEOUT_ERROR:
            success_list.append((expression, "TIMEOUT_ERROR", "TIMEOUT_ERROR"))
            continue
        elif cs480lab5main_error == cs480lab5main.MEMORY_ERROR:
            success_list.append((expression, "MEMORY_ERROR", "MEMORY_ERROR"))
            continue
        
        # if it's OverflowError or MemoryError, consider it successful
        try:
            # "(* might result in TypeError, e.g. log(*123)
            # "//" is interpreted as integer division by python
            # "**" is interpreted as exponentiation by python
            # "(^" gets changed to "(*"
            if "(*" in expression or "//" in expression or "**" in expression or "(^" in expression:
                raise SyntaxError
            
            # python doesn't detect NameError right away
            for s in expression_token_strings:
                if s[0].isalpha() and s not in cs480lab5main.FUNCTION_NAMES:
                    raise SyntaxError
            eval_expression = expression.replace("log", "log10")
            eval_expression = eval_expression.replace("ln", "log")
            eval_expression = eval_expression.replace("cot", "cot2")
            eval_expression = eval_expression.replace("{", "(")
            eval_expression = eval_expression.replace("}", ")")
            eval_expression = eval_expression.replace("^", "**")
            
            eval_result = eval(eval_expression)
            if isinstance(eval_result, float):
                eval_result = Decimal(eval_result)
        except (SyntaxError, NameError, TypeError):
            eval_result = "INVALID_EXPRESSION"
        except (ValueError, ZeroDivisionError):
            eval_result = "EVALUATION_ERROR"
        except OverflowError:
            success_list.append((expression, "OVERFLOW_ERROR", "OVERFLOW_ERROR"))
            continue
        except MemoryError:
            success_list.append((expression, "MEMORY_ERROR", "MEMORY_ERROR"))
            continue
        
        if isinstance(cs480lab5main_result, str) and isinstance(eval_result, str):
            passed = (cs480lab5main_result == eval_result)
        elif isinstance(cs480lab5main_result, str) or isinstance(eval_result, str):
            passed = False
        else:
            passed = (abs(cs480lab5main_result - eval_result) <= cfg_settings["max allowed error"])
        
        tuple_to_append = (expression, cs480lab5main_result, eval_result)
        
        if passed:
            success_list.append(tuple_to_append)
        else:
            failure_list.append(tuple_to_append)
    
    return (success_list, failure_list)


def get_random_expression(cfg_settings: Dict[str, Union[int, Decimal]], subexpression_depth: int = 0) -> List[str]:
    """
    Makes a list of strings representing the tokens of a random math expression.
    
    arguments:
        cfg_settings (Dict[str, Union[int, Decimal]]): Configuration settings to control how the expression is created.
        subexpression_depth (int): How deep the current expression is nested inside other expressions.
    
    return:
        List[str]: A list of strings representing the tokens of the math expression.
    """
    
    token_strings = []
    
    expression_length = randrange(1, cfg_settings["max subexpression values"])
    max_int = 10**cfg_settings["max digits in an int"]
    max_left_of_dot = 10**cfg_settings["max lefthand digits in a float"]
    max_right_of_dot = 10**cfg_settings["max righthand digits in a float"]
    
    for current_length in range(expression_length):
        
        # add unaries
        if randrange(2) == 1:
            how_many_unaries = randrange(1, cfg_settings["max consecutive unaries"])
            for _ in range(how_many_unaries):
                token_strings.append("+" if (randrange(2) == 1) else "-")
        
        # adding a number, function, or subexpression
        # don't add any more subexpressions or functions (since they contain subexpressions) if the current depth is already too low
        type_of_value = randrange(4 - (2 * (subexpression_depth >= cfg_settings["max subexpression depth"])))
        
        if type_of_value == 0: # int
            
            random_int = randrange(max_int)
            token_strings.append(str(random_int))
            
        elif type_of_value == 1: # float
            
            left_of_dot = randrange(max_left_of_dot)
            right_of_dot = randrange(max_right_of_dot)
            token_strings.append(str(left_of_dot) + "." + str(right_of_dot))
            
        elif type_of_value == 2: # function
            
            function_choice = cs480lab5main.FUNCTION_NAMES[randrange(len(cs480lab5main.FUNCTION_NAMES))]
            token_strings.append(function_choice)
            token_strings.append("(")
            token_strings.extend(get_random_expression(cfg_settings, subexpression_depth + 1))
            token_strings.append(")")
        
        elif type_of_value == 3: # subexpression
            
            parentheses_type = randrange(2)
            
            token_strings.append("(" if (parentheses_type == 0) else "{")
            token_strings.extend(get_random_expression(cfg_settings, subexpression_depth + 1))
            token_strings.append(")" if (parentheses_type == 0) else "}")
        
        # adding the next operator
        if current_length + 1 < expression_length:
            operator_choices = "+-*/^"
            
            exclude_exponent = (randrange(10) != 0) # don't allow ^ operator very often since it often causes timeouts
            operator_choice = operator_choices[randrange(len(operator_choices) - exclude_exponent)]
            token_strings.append(operator_choice)
    
    return token_strings


def add_an_error(expression_token_strings: List[str]) -> None:
    """
    Adds an error to a list of expression token strings.
    
    arguments:
        expression_token_strings (List[str]): The list of expression token strings to have an error added to.
    
    return:
        None
    """
    
    operator_choices = "+-*/^"
    operator_choices_no_unary = "*/^"
    
    idx = randrange(len(expression_token_strings))
    
    if expression_token_strings[idx] in cs480lab5main.FUNCTION_NAMES:
        
        # add an invalid token
        expression_token_strings[idx] += chr(randrange(ord("a"), ord("z") + 1))
        
    elif idx == len(expression_token_strings) - 1:
        
        # add an operator at the end
        expression_token_strings.append(operator_choices[randrange(len(operator_choices))])
        
    elif expression_token_strings[idx] in "({})":
        
        # cause parentheses to not be matched
        del expression_token_strings[idx]
        
    elif "." in expression_token_strings[idx]:
        
        # add extra dot to float
        expression_token_strings[idx] = expression_token_strings[idx] + "." + str(randrange(1000))
        
    elif expression_token_strings[idx].isdecimal() or expression_token_strings[idx] in operator_choices:
        
        expression_token_strings.insert(idx, operator_choices_no_unary[randrange(len(operator_choices_no_unary))])


def main() -> None:
    """
    The main function in the testing module.
    
    return:
        None
    """
    
    cs480lab5main.print2.testing = True
    
    cfg_file_name = "lab5_test_cfg.txt"
    log_file_name = "lab5_log.txt"
    
    directory_of_this_file = os.path.dirname(__file__)
    
    cfg_settings = {
        "random seed": None,
        "max subexpression values": None,
        "max subexpression depth": None,
        "max consecutive unaries": None,
        "max digits in an int": None,
        "max lefthand digits in a float": None,
        "max righthand digits in a float": None,
        "max allowed error": None,
        "timeout": None,
        "tests": None,
        "random error chance": None
    }
    
    try:
        with open(os.path.join(directory_of_this_file, cfg_file_name), "r") as infile:
            for line in infile:
                split_line = line.split(":")
                
                if len(split_line) < 2:
                    continue
                
                key = split_line[0]
                value = split_line[1].split()[0]
                
                if key in cfg_settings:
                    if key == "max allowed error" or key == "timeout":
                        cfg_settings[key] = abs(Decimal(value))
                    else:
                        cfg_settings[key] = abs(int(value))
        
        # checking if all the cfg settings were seen
        for value in cfg_settings.values():
            if value is None:
                raise ValueError
            
    except (FileNotFoundError, ValueError):
        print("couldn't read " + cfg_file_name + ". resetting " + cfg_file_name + "and using default testing settings.")
        cfg_settings = {
            "random seed": 0,
            "max subexpression values": 5,
            "max subexpression depth": 5,
            "max consecutive unaries": 5,
            "max digits in an int": 3,
            "max lefthand digits in a float": 3,
            "max righthand digits in a float": 3,
            "max allowed error": 0.00000001,
            "timeout": 0.01,
            "tests": 1000,
            "random error chance": 50
        }
        
        with open(os.path.join(directory_of_this_file, cfg_file_name), "w") as outfile:
            outfile.write(CFG_FILE_DEFAULT_TEXT)
    
    print("test settings:", *cfg_settings.items(), sep="\n")
    
    seed(cfg_settings["random seed"])
    
    cs480lab5main.check_timeout.timeout = cfg_settings["timeout"]
    try:
        results = run_tests(cfg_settings) # (non_error_test_passes, non_error_test_failures, error_test_passes, error_test_failures)
        
        print("successful tests:", len(results[0]), "\nfailed tests:", len(results[1]))
        
        with open(os.path.join(directory_of_this_file, log_file_name), "w") as outlogfile:
            
            outlogfile.write("\n- - - - - - - - - - - - - - - - -\nSUCCESSFUL TESTS\n- - - - - - - - - - - - - - - - -\n\n")
            for test in results[0]:
                outlogfile.write(
                    "EXPRESSION: " + test[0] + "\nCALCULATED VALUE: " + str(test[1]) + "\nCORRECT VALUE:    " + str(test[2]) + "\n\n"
                )
            
            outlogfile.write("\n- - - - - - - - - - - - - - - - -\nFAILED TESTS\n- - - - - - - - - - - - - - - - -\n\n")
            for test in results[1]:
                outlogfile.write(
                    "EXPRESSION: " + test[0] + "\nCALCULATED VALUE: " + str(test[1]) + "\nCORRECT VALUE:    " + str(test[2]) + "\n\n"
                )
        
    except SyntaxError as e:
        print("exception occurred while running tests:", e)
    
    print("testing finished")


if __name__ == "__main__":
    main()
