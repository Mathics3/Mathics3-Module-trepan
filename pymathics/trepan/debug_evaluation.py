"""
Additioal Mathics3 Functions added by Debugger.

This is similar to the mathics.builtin.trace module.
"""

import mathics.eval.tracing
from mathics.core.builtin import Builtin
from mathics.core.attributes import A_HOLD_ALL, A_PROTECTED
from mathics.core.evaluation import Evaluation

from pymathics.trepan.tracing import call_event_debug, debug_evaluate

class DebugEvaluation(Builtin):
    """
    ## <url>:trace native symbol:</url>

    <dl>
      <dt>'DebugEvaluation'[$expr$]
      <dd>Evaluate $expr$ inside the debugger
    </dl>

    >> DebugEvaluation[(x + x)^2]
     | ...
     = ...

    """

    attributes = A_HOLD_ALL | A_PROTECTED
    summary_text = "debug expression evaluation"

    def eval(self, expr, evaluation: Evaluation):
        "DebugEvaluation[expr_]"

        curr_trace_evaluation = evaluation.definitions.trace_evaluation

        old_evaluation_call_hook = mathics.eval.tracing.trace_evaluate_on_call
        old_evaluation_return_hook = mathics.eval.tracing.trace_evaluate_on_return

        old_hook_entry_fn = mathics.eval.tracing.hook_entry_fn
        old_hook_exit_fn = mathics.eval.tracing.hook_exit_fn

        old_evaluation_return_hook = mathics.eval.tracing.trace_evaluate_on_return


        mathics.eval.tracing.trace_evaluate_on_call = debug_evaluate

        mathics.eval.tracing.trace_evaluate_on_return = debug_evaluate
        mathics.eval.tracing.hook_entry_fn = call_event_debug
        mathics.eval.tracing.hook_exit_fn = call_event_debug


        evaluation.definitions.trace_evaluation = True
        try:
            return expr.evaluate(evaluation)
        except Exception:
            raise
        finally:
            evaluation.definitions.trace_evaluation = curr_trace_evaluation

            mathics.eval.tracing.trace_evaluate_on_call = old_evaluation_call_hook
            mathics.eval.tracing.trace_evaluate_on_return = old_evaluation_return_hook
            mathics.eval.tracing.hook_entry_fn = old_hook_entry_fn
            mathics.eval.tracing.hook_exit_fn = old_hook_exit_fn
