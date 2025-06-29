# -*- coding: utf-8 -*-
#   Copyright (C) 2025 Rocky Bernstein <rocky@gnu.org>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import types
from typing import Union
from trepan.lib.format import (
    Filename,
    LineNumber,
    format_token,
)
from mathics.builtin.patterns.basic import Blank, BlankNullSequence, BlankSequence
from mathics.builtin.patterns.composite import Pattern, OptionsPattern
from mathics.builtin.patterns.rules import RuleDelayed
from mathics.core.atoms import Atom
from mathics.core.builtin import Operator
from mathics.core.element import BaseElement
from mathics.core.expression import Expression
from mathics.core.list import ListExpression
from mathics.core.convert.op import operator_to_ascii
from mathics.core.parser.operators import (
    all_operators,
    flat_binary_operators,
    inequality_operators,
    left_binary_operators,
    misc_operators,
    nonassoc_binary_operators,
    postfix_operators,
    prefix_operators,
    right_binary_operators,
    ternary_operators,
)
from mathics.core.pattern import AtomPattern, ExpressionPattern
from mathics.core.rules import FunctionApplyRule, Rule
from mathics.core.symbols import Symbol, SymbolList
from mathics.core.systemsymbols import (
    SymbolBlank,
    SymbolBlankNullSequence,
    SymbolBlankSequence,
    SymbolPattern,
    SymbolRule,
    SymbolRuleDelayed,
)
from mathics_scanner.location import MATHICS3_PATHS, SourceRange
from mathics_pygments.lexer import MathematicaLexer
from pygments import highlight
from pygments.formatters import Terminal256Formatter

# Constant to force no parenthesis. This
# is used to make sure we don't add parenthsis when the
# next symbol is not an operator.
NO_PARENTHESIS_PRECEDENCE = 10000

# from mathics.builtin.pattern import Pattern

flat_binary_operator_set = set(flat_binary_operators.keys())
inequality_operator_set = set(inequality_operators)
left_binary_operator_set = set(left_binary_operators.keys())
misc_operator_set = set(misc_operators.keys())
nonassoc_binary_operators_set = set(nonassoc_binary_operators.keys())
postfix_operator_set = set(postfix_operators.keys())
prefix_operator_set = set(prefix_operators.keys())
right_binary_operator_set = set(right_binary_operators.keys())
ternary_operator_set = set(ternary_operators.keys())

binary_operator_set = (
    flat_binary_operator_set
    | inequality_operator_set
    | left_binary_operator_set
    | right_binary_operator_set
)

all_operator_set = (
    binary_operator_set
    | misc_operator_set
    | nonassoc_binary_operators_set
    | postfix_operator_set
    | prefix_operator_set
    | ternary_operator_set
)

mma_lexer = MathematicaLexer()


def format_list(elements: tuple) -> str:
    """
    Return Mathics3 string using the elements of a List[]
    M-expression or ListExpression object
    """
    return "{%s}" % (", ".join([format_element(element) for element in elements]),)


def format_pattern(elements: tuple) -> str:
    """
    Return Mathics3 string using the elemnents of a Pattern[] M-expression
    or Pattern object
    """
    assert len(elements) == 2
    first_arg = elements[0]
    second_arg = elements[1]
    return f"{format_element(first_arg)}:{format_element(second_arg, use_operator_form=True)}"


def format_element(
    element: BaseElement, allow_python=False, use_operator_form=False
) -> str:
    """Formats a Mathics3 element more like the way it might be
    entered in Mathics3, hiding some of the internal Element representation.

    This includes removing some context markers on symbols, or
    internal object representations like ListExpression.

    """

    def maybe_parenthesize_operand(precedence: int, operand) -> str:
        """
        format operand into a string and surround it with parenethesis
           if it needs it. The need for parenthesis is determined by
           `precedence` and precedence of `operand`.
        """
        child_precedence = get_operator_precedence(operand)
        child_str = format_element(
            operand, use_operator_form=use_operator_form
            )
        if child_precedence < precedence:
            child_str = f"({child_str})"
        return child_str

    if allow_python:
        if isinstance(element, (list, tuple)):
            aggregate_function = "list" if isinstance(element, list) else "tuple"
            fn_args = ", ".join(
                [
                    format_element(
                        element=e,
                        allow_python=allow_python,
                        use_operator_form=use_operator_form,
                    )
                    for e in element
                ]
            )
            return f"{aggregate_function}({fn_args})"
        elif isinstance(element, dict):
            return (
                "{\n  "
                + (
                    ",\n  ".join(
                        [
                            f"{format_element(key, use_operator_form=use_operator_form)}: {format_element(value, use_operator_form=use_operator_form)}"
                            for key, value in element.items()
                        ]
                    )
                )
                + "\n}"
            )

    if isinstance(element, Symbol):
        return element.short_name
    elif isinstance(element, Atom):
        return str(element)
    elif isinstance(element, AtomPattern):
        return element.get_name(short=True)
    elif isinstance(element, (Blank, BlankNullSequence, BlankSequence)):
        if isinstance(element, Blank):
            name = "_"
        elif isinstance(element, BlankSequence):
            name = "__"
        else:
            name = "___"

        if len(element.expr.elements) == 0:
            return name
        else:
            return (
                f"{name}"
                f"{', '.join([format_element(element, use_operator_form=use_operator_form) for element in element.elements])}"
            )

    elif isinstance(element, FunctionApplyRule):
        function_class = element.function.__self__.__class__
        function_name = f"{function_class.__module__}.{function_class.__name__}"
        return f"{format_element(element.pattern, use_operator_form=use_operator_form)} -> {function_name}()"
    # Note ListExpression test has to come before Expression test since
    # ListExpression is a subclass of Expression
    elif isinstance(element, ListExpression):
        return format_list(element.elements)
    elif isinstance(element, (Expression, ExpressionPattern, Operator)):
        head = element.head
        # We handle printing "Expression"s which haven't been
        # converted to an internal data structure yet for example
        # Expression[List, Integer1, Integer2] instead of
        # ListExpression[Integer1, Integer2]

        if head is SymbolList:
            return format_list(element.elements)
        elif head is SymbolPattern and len(element.elements) == 2:
            return format_pattern(element.elements)
        elif head is SymbolRule:
            return f"{format_element(element.elements[0], use_operator_form=use_operator_form)} -> {format_element(element.elements[1], use_operator_form=use_operator_form)}"
        elif head is SymbolRuleDelayed:
            return f"{format_element(element.elements[0], use_operator_form=use_operator_form)} :> {format_element(element.elements[1], use_operator_form=use_operator_form)}"
        elif head in (SymbolBlank, SymbolBlankNullSequence, SymbolBlankSequence):
            if head is SymbolBlank:
                name = "_"
            elif head is SymbolBlankSequence:
                name = "__"
            else:
                name = "___"

            if len(element.elements) == 0:
                return name
            else:
                expr_str = ", ".join(
                    [
                        format_element(element, use_operator_form=use_operator_form)
                        for element in element.elements
                    ]
                )
                return f"{name} {expr_str}"

        elif (
            use_operator_form
            and hasattr(head, "short_name")
            and head.short_name in all_operator_set
        ):
            operator_name = head.short_name
            if operator_name in binary_operator_set:
                operator_str = operator_to_ascii.get(operator_name, None)
                if operator_str is not None:
                    precedence = get_operator_precedence(element)
                    result = []
                    for operand in element.elements[:-1]:
                        child_str = maybe_parenthesize_operand(precedence, operand)
                        result.append(child_str)
                        result.append(operator_str)

                    child_str = maybe_parenthesize_operand(precedence, element.elements[-1])
                    result.append(child_str)
                    return " ".join(result)
                pass
            elif operator_name in prefix_operator_set:
                operator_str = operator_to_ascii.get(operator_name, None)
                if operator_str is not None and len(element.elements) == 1:
                    precedence = get_operator_precedence(element)
                    child_str = maybe_parenthesize_operand(precedence, element.elements[0])
                    return (
                        operator_str
                        + f"{format_element(element.elements[0], use_operator_form=use_operator_form)}"
                    )
            elif operator_name in postfix_operator_set:
                operator_str = operator_to_ascii.get(operator_name, None)
                if operator_str is not None and len(element.elements) == 1:
                    precedence = get_operator_precedence(element)
                    child_str = maybe_parenthesize_operand(precedence, element.elements[0])
                    return (
                        f"{child_str}"
                        + operator_str
                    )
            return f"{format_element(head)}[%s]" % (
                ", ".join(
                    [
                        format_element(element, use_operator_form=use_operator_form)
                        for element in element.elements
                    ]
                ),
            )

        else:
            # A general Expression.
            return (
                f"{format_element(head, use_operator_form=use_operator_form)}[%s]"
                % (
                    ", ".join(
                        [
                            format_element(element, use_operator_form=use_operator_form)
                            for element in element.elements
                        ]
                    ),
                )
            )
    elif isinstance(element, OptionsPattern):
        return "{%s}" % (
            ", ".join(
                [
                    format_element(element, use_operator_form=use_operator_form)
                    for element in element.elements
                ]
            ),
        )
    # FIXME handle other than 2 arguments...
    elif isinstance(element, Pattern) and len(element.elements) == 2:
        return format_pattern(element.elements)
    elif isinstance(element, Rule):
        return (
            f"{format_element(element.pattern, use_operator_form=use_operator_form)} "
            f"-> {format_element(element.replace, use_operator_form=use_operator_form)}"
        )
    elif isinstance(element, RuleDelayed):
        return (
            f"{format_element(element.pattern)} :> "
            "{format_element(element.replace, use_operator_form=use_operator_form)}"
        )
    elif isinstance(element, types.FunctionType):
        return f"<Python function {element.__qualname__}>"
    return str(element)


def format_location(style: str, loc: Union[SourceRange, types.MethodType]) -> str:
    """
    Given Location ``loc`` return a string representation of that
    """
    if isinstance(loc, types.MethodType):
        func = loc.__func__
        doc = func.__doc__
        code = func.__code__
        formatted_doc = "" if doc is None else pygments_format(doc, style)
        filename = {code.co_filename}
        line_number = code.co_firstlineno
        return "%s %s at line %s" % (
            formatted_doc,
            format_token(Filename, filename, style=style),
            format_token(LineNumber, str(line_number), style=style),
            )

    filename = MATHICS3_PATHS[loc.container]
    if loc.start_line == loc.end_line:
        # return "%s at line %s:%s-%s" % (
            # format_token(Filename, filename, style=style),
            # format_token(LineNumber, str(loc.start_line), style=style),
            # format_token(LineNumber, str(loc.start_pos), style=style),
            # format_token(LineNumber, str(loc.end_pos), style=style),
        return "(%s:%s): <module>" % (filename, loc.start_line)
    else:
        return "%s at line %s:%s-%s-%s" % (
            format_token(Filename, filename, style=style),
            format_token(LineNumber, str(loc.start_line), style=style),
            format_token(LineNumber, str(loc.start_pos), style=style),
            format_token(LineNumber, str(loc.endt_line), style=style),
            format_token(LineNumber, str(loc.end_pos), style=style),
            )

def get_operator_precedence(element) -> int:
    if not isinstance(element, (Expression, ExpressionPattern)):
        return NO_PARENTHESIS_PRECEDENCE
    head = element.head
    operator_name = head.short_name
    if operator_name in all_operators:
        operator_str = operator_to_ascii.get(operator_name, None)
        if operator_str is not None:
            return all_operators[operator_name]

    return NO_PARENTHESIS_PRECEDENCE


def pygments_format(mathics_str: str, style) -> str:
    """Add terminial formatting for a Mathics3 string
    ``mathics_str``, using pygments style ``style``.
    """
    if style is None:
        return mathics_str
    terminal_formatter = Terminal256Formatter(style=style)
    return highlight(mathics_str, mma_lexer, terminal_formatter)
