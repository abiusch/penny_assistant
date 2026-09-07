"""Bounded arithmetic for the registered calculator, without Python eval."""

import ast
import math
import operator


MAX_EXPRESSION_LENGTH = 200
MAX_NODES = 100
MAX_DEPTH = 20
MAX_INTEGER_BITS = 4096
MAX_EXPONENT = 4096


def _number(value):
    if type(value) not in (int, float):
        raise ValueError('Only real numbers are supported')
    if isinstance(value, int):
        if value.bit_length() > MAX_INTEGER_BITS:
            raise ValueError('Calculation exceeds the integer size limit')
    elif not math.isfinite(value):
        raise ValueError('Calculation requires finite numbers')
    return value


def _power(base, exponent, modulus=None):
    _number(base)
    _number(exponent)
    if abs(exponent) > MAX_EXPONENT:
        raise ValueError('Calculation exceeds the exponent limit')
    if modulus is None:
        if isinstance(base, int) and isinstance(exponent, int) and exponent > 0:
            if (abs(base).bit_length() - 1) * exponent > MAX_INTEGER_BITS:
                raise ValueError('Calculation exceeds the integer size limit')
        return _number(pow(base, exponent))
    return _number(pow(base, exponent, _number(modulus)))


def evaluate(expression):
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError('Expression must be a non-empty string')
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError('Expression too long (max 200 chars)')
    tree = ast.parse(expression.strip(), mode='eval')
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise ValueError('Calculation exceeds the complexity limit')

    def visit(node, depth=0):
        if depth > MAX_DEPTH:
            raise ValueError('Calculation exceeds the nesting limit')
        if isinstance(node, ast.Constant):
            return _number(node.value)
        if isinstance(node, ast.Tuple):
            return tuple(_number(visit(item, depth + 1)) for item in node.elts)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = _number(visit(node.operand, depth + 1))
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left = _number(visit(node.left, depth + 1))
            right = _number(visit(node.right, depth + 1))
            if isinstance(node.op, ast.Pow):
                return _power(left, right)
            operations = {ast.Add: operator.add, ast.Sub: operator.sub,
                          ast.Mult: operator.mul, ast.Div: operator.truediv,
                          ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
                          ast.BitXor: operator.xor}
            operation = operations.get(type(node.op))
            if operation is None:
                raise ValueError('Unsupported arithmetic operator')
            # Each operand is already bounded. Even multiplication allocates
            # at most twice the allowed bit count before the result is checked.
            return _number(operation(left, right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            args = [visit(arg, depth + 1) for arg in node.args]
            name = node.func.id
            if name == 'pow' and len(args) in (2, 3):
                return _power(*args)
            if name == 'abs' and len(args) == 1:
                return abs(_number(args[0]))
            if name == 'round' and len(args) in (1, 2):
                _number(args[0])
                if len(args) == 2 and (type(args[1]) is not int or abs(args[1]) > MAX_EXPONENT):
                    raise ValueError('Rounding precision exceeds the limit')
                return _number(round(*args))
            if name == 'sum' and len(args) in (1, 2) and isinstance(args[0], tuple):
                start = _number(args[1]) if len(args) == 2 else 0
                return _number(sum(args[0], start))
            if name in ('min', 'max'):
                values = args[0] if len(args) == 1 and isinstance(args[0], tuple) else args
                if not values:
                    raise ValueError('Expected at least one number')
                values = [_number(value) for value in values]
                return (min if name == 'min' else max)(values)
            raise ValueError('Unsupported function or arguments')
        raise ValueError('Unsupported expression; use arithmetic and approved math functions')

    return _number(visit(tree.body))


def calculate(args):
    """Keep the tool's existing expression/equation input and text output."""
    expression = args.get('expression') or args.get('equation', '')
    if not expression:
        return 'ERROR: No expression provided'
    try:
        return f'CALCULATION RESULT:\n{expression} = {evaluate(expression)}'
    except (ValueError, TypeError, SyntaxError, ArithmeticError) as error:
        return f'ERROR: Calculation failed: {error}'
