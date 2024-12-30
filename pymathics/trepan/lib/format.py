from mathics.builtin.patterns.basic import Blank, BlankNullSequence, BlankSequence
from mathics.builtin.patterns.composite import Pattern, OptionsPattern
from mathics.builtin.patterns.rules import RuleDelayed
from mathics.core.atoms import Atom
from mathics.core.element import BaseElement
from mathics.core.expression import Expression
from mathics.core.list import ListExpression
from mathics.core.convert.op import ascii_operator_to_symbol
from mathics.core.parser.operators import (
    flat_binary_ops,
    inequality_ops,
    left_binary_ops,
    misc_ops,
    nonassoc_binary_ops,
    postfix_ops,
    prefix_ops,
    right_binary_ops,
    ternary_ops,
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
from mathics_pygments.lexer import MathematicaLexer
from pygments import highlight
from pygments.formatters import Terminal256Formatter

# from mathics.builtin.pattern import Pattern

symbol_name_to_ascii_operator = {
    symbol_name: ascii_operator
    for ascii_operator, symbol_name in ascii_operator_to_symbol.items()
}
flat_binary_operator_set = set(flat_binary_ops.keys())
inequality_operator_set = set(inequality_ops)
left_binary_operator_set = set(left_binary_ops.keys())
misc_operator_set = set(misc_ops.keys())
nonassoc_binary_ops_set = set(nonassoc_binary_ops.keys())
postfix_operator_set = set(postfix_ops.keys())
prefix_operator_set = set(prefix_ops.keys())
right_binary_operator_set = set(right_binary_ops.keys())
ternary_operator_set = set(ternary_ops.keys())

binary_operator_set = (
    flat_binary_operator_set
    | inequality_operator_set
    | left_binary_operator_set
    | right_binary_operator_set
)

all_operators = (
    binary_operator_set
    | misc_operator_set
    | nonassoc_binary_ops_set
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
    return f"{format_element(first_arg)}{format_element(second_arg)}"


def format_element(
    element: BaseElement, allow_python=False, use_operator_form=False
) -> str:
    """Formats a Mathics3 element more like the way it might be
    entered in Mathics3, hiding some of the internal Element representation.

    This includes removing some context markers on symbols, or
    internal object representations like ListExpression.

    """
    if allow_python:
        if isinstance(element, (list, tuple)):
            aggregate_function = "list" if isinstance(element, list) else "tuple"
            return (
                f"{aggregate_function}("
                f"{', '.join([format_element(e, use_operator_form=use_operator_form) for e in element])})"
            )
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
    elif isinstance(element, (Expression, ExpressionPattern)):
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
            and head.short_name in all_operators
        ):
            operator_name = head.short_name
            if operator_name in binary_operator_set:
                operator_str = symbol_name_to_ascii_operator.get(operator_name, None)
                if operator_str is not None:
                    result = []
                    for operand in element.elements[:-1]:
                        result.append(
                            format_element(operand, use_operator_form=use_operator_form)
                        )
                        result.append(operator_str)
                    result.append(
                        format_element(
                            element.elements[-1], use_operator_form=use_operator_form
                        )
                    )
                    return " ".join(result)
                pass
            elif operator_name in prefix_operator_set:
                operator_str = symbol_name_to_ascii_operator.get(operator_name, None)
                if operator_str is not None and len(element.elements) == 1:
                    return (
                        operator_str
                        + f"{format_element(element.elements[0], use_operator_form=use_operator_form)}"
                    )
            elif operator_name in postfix_operator_set:
                operator_str = symbol_name_to_ascii_operator.get(operator_name, None)
                if operator_str is not None and len(element.elements) == 1:
                    return (
                        f"{format_element(element.elements[0], use_operator_form=use_operator_form)}"
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
    return str(element)


def pygments_format(mathics_str: str, style) -> str:
    """Add terminial formatting for a Mathics3 string
    ``mathics_str``, using pygments style ``style``.
    """
    if style is None:
        return mathics_str
    terminal_formatter = Terminal256Formatter(style=style)
    return highlight(mathics_str, mma_lexer, terminal_formatter)
