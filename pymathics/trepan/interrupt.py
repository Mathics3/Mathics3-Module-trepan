"""
Default Mathics3 Interrupt routines.

Note: other environments may build on or use other interrupt handlers
"""

import signal
import subprocess
import mathics.eval.tracing as tracing
from typing import Optional
from types import FrameType

from mathics import settings
from mathics.core.evaluation import Evaluation
from mathics.core.interrupt import ReturnInterrupt, TimeoutInterrupt
from mathics.eval.stackframe import get_eval_Expression
from pymathics.trepan.lib.exception import DebuggerQuitException
from pymathics.trepan.tracing import call_event_debug
from pymathics.trepan import Debugger

from trepan.lib.format import format_element


# See also __main__'s interactive_eval_loop
def inspect_eval_loop(evaluation: Evaluation):
    """
    A read eval/loop for an Interrupt's "inspect" command.
    """
    shell = evaluation.shell
    if shell is not None:
        was_inside_interrupt = shell.is_inside_interrupt
        shell.is_inside_interrupt = True
    else:
        was_inside_interrupt = False

    previous_recursion_depth = evaluation.recursion_depth
    while True:
        try:
            # Reset line number within an In[] line number.
            # Note: this is not setting as, say, In[5]
            # to back to In[1], but instead it sets the line number position *within*
            # In[5]. The user input for "In[5]" might have several continuation lines.
            if shell is not None and hasattr(shell, "lineno"):
                shell.lineno = 0

            query, source_code = evaluation.parse_feeder_returning_code(shell)
            # show_echo(source_code, evaluation)
            if len(source_code) and source_code[0] == "!" and shell is not None:
                subprocess.run(source_code[1:], shell=True)
                if shell.definitions is not None:
                    shell.definitions.increment_line_no(1)
                continue
            if query is None:
                continue
            result = evaluation.evaluate(query, timeout=settings.TIMEOUT)
            if result is not None and shell is not None:
                shell.print_result(result, strict_wl_output=True)
        except TimeoutInterrupt:
            shell.errmsg("\nTimeout occurred - ignored.")
            pass
        except ReturnInterrupt:
            evaluation.last_eval = None
            evaluation.exc_result = None
            evaluation.message("Interrupt", "dgend")
            raise
        except KeyboardInterrupt:
            shell.errmsg("\nKeyboardInterrupt")
        except EOFError:
            print()
            raise
        except SystemExit:
            # raise to pass the error code on, e.g. Quit[1]
            raise
        finally:
            evaluation.recursion_depth = previous_recursion_depth
            if shell is not None:
                shell.is_inside_interrupt = was_inside_interrupt


def Mathics3_trepan_signal_handler(sig: int, interrupted_frame: Optional[FrameType]):
    """
    Custom signal handler for SIGINT (Ctrl+C). When we get this signal,
    go into the Trepan debugger REPL.
    """
    evaluation: Optional[Evaluation] = None

    # Find an evaluation object to pass to the Mathics3 interrupt handler
    while interrupted_frame is not None:
        if (
            evaluation := interrupted_frame.f_locals.get("evaluation")
        ) is not None and isinstance(evaluation, Evaluation):
            break
        interrupted_frame = interrupted_frame.f_back
    print_fn = evaluation.print_out if evaluation is not None else print
    print_fn("")
    if interrupted_frame is None:
        print("Unable to find Evaluation frame to start on")
        return

    try:
        call_event_debug(tracing.TraceEvent.interrupt, Debugger.eval, evaluation)
    except DebuggerQuitException:
        # Go back into mathics.
        pass

def Mathics3_trepan_USR1_handler(sig: int, interrupted_frame: FrameType):
    """
    Custom signal handler for SIGUSR1. When we get this signal, try to
   find an Expression that is getting evaluated, and print that. Then
   continue.
    """
    get_eval_Expression()
    if (eval_expression := get_eval_Expression()) is not None:
        eval_expression_str = format_element(eval_expression, allow_python=False, use_operator_form=True)
        print(f"Expression: {eval_expression_str}")


def setup_signal_handler():
    signal.signal(signal.SIGINT, Mathics3_trepan_signal_handler)
    signal.signal(signal.SIGUSR1, Mathics3_trepan_USR1_handler)
