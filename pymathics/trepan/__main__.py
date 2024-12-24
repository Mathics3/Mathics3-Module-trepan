"""
Mathics3 Debugger Builtin Functions

These functions allow you to set events for entering the debugger when \
an event is triggered, or enter the debugger immediately.
"""

import inspect
import mathics.core as mathics_core
import mathics.core.parser
import mathics.eval.files_io.files as io_files
import mathics.eval.tracing as tracing

from mathics.core.atoms import String
from mathics.core.builtin import Builtin
from mathics.core.evaluation import Evaluation
from mathics.core.list import ListExpression
from mathics.core.rules import FunctionApplyRule
from mathics.core.symbols import SymbolFalse, SymbolTrue

from pymathics.trepan.tracing import (
    TraceEventNames,
    # apply_builtin_box_fn_traced,
    apply_builtin_fn_print,
    apply_builtin_fn_traced,
    call_event_debug,
    call_event_get,
    call_trepan3k,
    debug_evaluate,
    event_filters,
    pre_evaluation_debugger_hook,
    trace_evaluate,
)

from typing import Dict, Optional, Tuple

# FIXME: DRY with debugger.tracing.TraceEventNames
EVENT_OPTIONS: Dict[str, str] = {
    "Get": "False",
    "Numpy": "False",
    "SymPy": "False",
    "apply": "False",
    "applyBox": "False",
    "evaluation": "False",
    "evalMethod": "False",
    "evalFunction": "False",
    "mpmath": "False",
    "parse": "False",
}

parse_untraced = mathics.core.parser.parse

# FIXME:

# We assume FunctionApplyRule.apply_function hasn't previously been
# overwritten at LoadModule["pymathics.trepan"] time, so
# the below save to EVALUATION_APPLY is pristine.
# Eventually we might change  mathics.core.rules.FunctionApplyRule
# in some way to make this more robust.
EVALUATION_APPLY = FunctionApplyRule.apply_function


class DebugActivate(Builtin):
    """
    <dl>
      <dt>'DebugActivate'[$options$]
      <dd>Set to enter debugger entry on certain event
    </dl>

    $options$ include:
    <ul>
      <li>'Get':  debug Get[] calls, with Trace->True set
      <li>'NumPy':  debug NumPy calls
      <li>'SymPy': debug SymPy calls
      <li>'mpmath': debug mpmath calls
      <li>'apply'; debug function apply calls that are <i>not</i> boxing \
          routines
      <li>'applyBox'; debug function apply calls that <i>are</i> boxing \
          routines
    </ul>

    >> DebugActivate[SymPy -> True]
     = ...
    """

    messages = {
        "opttname": "mpmath name `1` is not a String",
        "opttype": "mpmath option `1` should be a boolean or a list",
    }
    options = EVENT_OPTIONS
    summary_text = """set events to go into the Mathics3 Debugger REPL"""

    # The function below should start with "eval"
    def eval(self, evaluation: Evaluation, options: dict):
        "DebugActivate[OptionsPattern[DebugActivate]]"

        def validate_option(
            option, evaluation: Evaluation
        ) -> Tuple[Optional[list], bool]:
            """
            Checks that `option` is valid; it should either be a String, a
            Mathics3 boolean, or a List of Mathics3 String.

            The return is a tuple of the filter expression and a boolean
            indicating wither `option` was valid. Recall that a filter of
            "None" means don't filter at all - accept anything.
            """
            if isinstance(option, ListExpression):
                filters = []
                for elt in option.elements:
                    # TODO: accept a Symbol look up for {mpmath, SymPy, Numpy} name-ness
                    if not isinstance(elt, String):
                        evaluation.message("DebugActivate", "opttname", option)
                        return None, False
                    # TODO: check that string is a valid {mpmath, SymPy, Numpy} name.
                    # THINK ABOUT: if a filter value is a short name, e.g. "Plus" instead of
                    # "System`Plus", should we try to fill in the full name? Or use "Plus"
                    # as a way to match any "XXX`YYY..`Plus" that might appear in any
                    # context in the future.
                    filters.append(elt.value)
                return filters, True
            elif option in (SymbolTrue, SymbolFalse):
                return (None, True)
            elif isinstance(option, String):
                # TODO: check that string is a valid {mpmath, SymPy, NumPy} name
                return ([option.value], True)
            else:
                evaluation.message("DebugActivate", "opttype", option)
                return None, False

        for event_name in TraceEventNames:
            if event_name == "Debugger":
                continue
            option = self.get_option(options, event_name, evaluation)
            if option is None:
                evaluation.message("DebugActivate", "options", event_name)
                break

            filters, is_valid = validate_option(option, evaluation)
            if not is_valid:
                break

            event_is_debugged = option == SymbolTrue or isinstance(
                option, (ListExpression, String)
            )
            if event_is_debugged:
                tracing.hook_entry_fn = call_event_debug
                tracing.hook_exit_fn = tracing.return_event_print

            if event_name == "Get":
                io_files.GET_PRINT_FN = (
                    call_event_get
                    if event_is_debugged
                    else io_files.print_line_number_and_text
                )
            elif event_name == "SymPy":
                event_filters["SymPy"] = filters
                tracing.run_sympy = (
                    tracing.run_sympy_traced if event_is_debugged else tracing.run_fast
                )

            # FIXME: we need to fold in whether to track boxing or not
            # into apply_function(). As things stand now the single
            # monkey-patched routine is clobbered by applyBox below
            elif event_name == "apply":
                FunctionApplyRule.apply_function = (
                    apply_builtin_fn_traced if event_is_debugged else EVALUATION_APPLY
                )
            elif event_name == "evaluation":
                event_filters["evaluate-entry"] = event_filters["evaluate-result"] = (
                    filters
                )
                tracing.trace_evaluate_on_return = tracing.trace_evaluate_on_call = (
                    debug_evaluate if event_is_debugged else None
                )

            elif event_name == "evalMethod":
                event_filters["evalMethod"] = filters
                mathics_core.PRE_EVALUATION_HOOK = (
                    pre_evaluation_debugger_hook if event_is_debugged else None
                )
            elif event_name == "mpmath":
                event_filters["mpmath"] = filters
                tracing.run_mpmath = (
                    tracing.run_mpmath_traced if event_is_debugged else tracing.run_fast
                )
            # FIXME: see above.
            # elif event_name == "applyBox":
            #     FunctionApplyRule.apply_function = (
            #         apply_builtin_box_fn_traced if event_is_debugged else EVALUATION_APPLY
            #     )
        # print("XXX", event_filters)


class Debugger(Builtin):
    """
    <dl>
      <dt>'Debugger'[trepan3k -> True]
      <dd>enter debugger entry on certain event
    </dl>

    X> Debugger[]
     = ...

    X> Debugger[trepan3k -> True]
     = ...
    """

    options = {"trepan3k": "False"}
    summary_text = """get into Mathics3 Debugger REPL"""

    def eval(self, evaluation: Evaluation, options: dict):
        "Debugger[OptionsPattern[Debugger]]"
        if self.get_option(options, "trepan3k", evaluation) == SymbolTrue:
            global dbg
            if dbg is None:
                from pymathics.trepan.lib.repl import DebugREPL

                dbg = DebugREPL()

            frame = inspect.currentframe()
            if frame is not None:
                dbg.core.processor.curframe = frame.f_back
                call_trepan3k(dbg.core.processor)
            else:
                print("Error getting current frame")

        else:
            call_event_debug(tracing.TraceEvent.debugger, Debugger.eval, evaluation)


class TraceActivate(Builtin):
    """
    <dl>
      <dt>'TraceActivate'[$options$]
      <dd>Set event tracing and debugging.
    </dl>

    >> TraceActivate[SymPy -> True]
     = ...
    """

    options = EVENT_OPTIONS
    summary_text = """Set/unset tracing and debugging"""

    def eval(self, evaluation: Evaluation, options: dict):
        "TraceActivate[OptionsPattern[TraceActivate]]"

        # DRY with TraceActivate
        def validate_option(
            option, evaluation: Evaluation
        ) -> Tuple[Optional[list], bool]:
            """
            Checks that `option` is valid; it should either be a
            String, a Mathics3 boolean, or a List of Mathics3 String.

            The return is a tuple of the filter expression and a
            boolean indicating whether `option` was valid. Recall that
            a filter of None means don't filter at all - except
            anything.

            """
            if isinstance(option, ListExpression):
                filters = []
                for elt in option.elements:
                    # TODO: accept a Symbol look up for {mpmath,
                    # SymPy, Numpy} name-ness
                    if not isinstance(elt, String):
                        evaluation.message("DebugActivate", "opttname", option)
                        return None, False
                    # TODO: check that string is a valid {mpmath,
                    # SymPy, Numpy} name.
                    filters.append(elt.value)
                return filters, True
            elif option in (SymbolTrue, SymbolFalse):
                return (None, True)
            elif isinstance(option, String):
                # TODO: check that string is a valid {mpmath, SymPy,
                # NumPy} name
                return ([option.value], True)
            else:
                evaluation.message("DebugActivate", "opttype", option)
                return None, False

        # adjust_event_handlers(self, evaluation, options)
        for event_name in TraceEventNames:

            if event_name == "Debugger":
                continue
            option = self.get_option(options, event_name, evaluation)
            if option is None:
                evaluation.message("TraceActivate", "options", event_name)
                break

            filters, is_valid = validate_option(option, evaluation)
            if not is_valid:
                break

            event_is_traced = option == SymbolTrue
            if event_is_traced:
                tracing.hook_entry_fn = tracing.call_event_print
                tracing.hook_exit_fn = tracing.return_event_print
            if event_name == "Get":
                io_files.GET_PRINT_FN = (
                    io_files.print_line_number_and_text if event_is_traced else None
                )
            elif event_name == "SymPy":
                event_filters["SymPy"] = filters
                tracing.run_sympy = (
                    tracing.run_sympy_traced if event_is_traced else tracing.run_fast
                )
            elif event_name == "apply":
                FunctionApplyRule.apply_function = (
                    apply_builtin_fn_print if event_is_traced else EVALUATION_APPLY
                )
            elif event_name == "evaluation":
                event_filters["evaluation"] = filters
                tracing.trace_evaluate_on_return = tracing.trace_evaluate_on_call = (
                    trace_evaluate if event_is_traced else None
                )
            elif event_name == "evalMethod":
                event_filters["evalMethod"] = filters
                mathics_core.PRE_EVALUATION_HOOK = (
                    apply_builtin_fn_print if event_is_traced else None
                )
            elif event_name == "applyBox":
                event_filters["mpmath"] = filters
                FunctionApplyRule.apply_function = (
                    apply_builtin_fn_print if event_is_traced else EVALUATION_APPLY
                )
            elif event_name == "mpmath":
                tracing.run_mpmath = (
                    tracing.run_mpmath_traced if event_is_traced else tracing.run_fast
                )
