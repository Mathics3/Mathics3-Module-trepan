import inspect
from math import log10

from mathics.builtin.trace import _TraceBase
from mathics.core.evaluation import Evaluation
from mathics.core.expression import Expression
from mathics.core.symbols import SymbolNull
from mathics.eval.symbolic_history.stack import is_showable_frame

from pymathics.trepan.lib.format import format_element, pygments_format
from pymathics.trepan.lib.stack import format_eval_builtin_fn


def eval_Stacktrace():
    """
    Replacement for mathics.eval.eval_Stacktrace.
    """

    global dbg
    if dbg is None:
        from pymathics.trepan.lib.repl import DebugREPL

        dbg = DebugREPL()

    frame = inspect.currentframe()
    assert frame is not None
    frame = frame.f_back
    frame_number = -2

    frames = []
    last_frame_str = None
    while frame is not None:
        is_builtin, self_obj = is_showable_frame(frame)
        if is_builtin:
            # The two frames are always Stacktrace[]
            # and Evaluate of that. So skip these.
            if frame_number > 0:
                if isinstance(self_obj, Expression):
                    expr_str = format_element(self_obj)
                    frame_str = pygments_format(expr_str, dbg.settings["style"])
                else:
                    frame_str = format_eval_builtin_fn(frame, dbg.settings["style"])
                if last_frame_str != frame_str:
                    frames.append(frame_str)
                    last_frame_str = frame_str
            frame_number += 1
        frame = frame.f_back

    # FIXME this should done in a separate function and the
    # we should return the above.
    n = len(frames)
    max_width = int(log10(n + 1)) + 1
    number_template = "%%%dd" % max_width
    for frame_number, frame_str in enumerate(frames):
        formatted_frame_number = number_template % (n - frame_number)
        dbg.core.processor.msg_nocr(f"{formatted_frame_number}: {frame_str}")
    pass

class Stacktrace(_TraceBase):
    """
    ## <url>:trace native symbol:</url>

    <dl>
      <dt>'Stacktrace[]'
      <dd>Print Mathics3 stack trace of evalutations leading to this point
    </dl>

    To show the Mathics3 evaluation stack at the \
    point where expression $expr$ is evaluated, wrap $expr$ inside '{$expr$ Stacktrace[]}[1]]' \
    or something similar.

    Here is a complete example. To show the evaluation stack when computing a homegrown \
    factorial function:

    >> F[0] := {1, Stacktrace[]}[[1]]; F[n_] := n * F[n-1]

    >> F[3] (* See console log *)
     = 6

    The actual 'Stacktrace[0]' call is hidden from the output; so when \
    run on its own, nothing appears.

    >> Stacktrace[]

    #> Clear[F]
    """

    summary_text = "print Mathics3 function stacktrace"

    def eval(self, evaluation: Evaluation):
        "Stacktrace[]"

        eval_Stacktrace()
        return SymbolNull
