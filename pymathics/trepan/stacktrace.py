import inspect
from math import log10

from mathics.core.expression import Expression
from mathics.eval.trace import is_showable_frame

from pymathics.trepan.lib.format import format_element, pygments_format
from pymathics.trepan.lib.stack import format_eval_builtin_fn
from pymathics.trepan.tracing import dbg


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
    last_was_eval = False

    frames = []
    while frame is not None:
        is_builtin, self_obj = is_showable_frame(frame)
        if is_builtin:
            # The two frames are always Stacktrace[]
            # and Evaluate of that. So skip these.
            if frame_number > 0 and not last_was_eval:
                if isinstance(self_obj, Expression):
                    last_was_eval = False
                    expr_str = format_element(self_obj)
                    frame_str = pygments_format(expr_str, dbg.settings["style"])
                else:
                    last_was_eval = True
                    frame_str = format_eval_builtin_fn(frame, dbg.settings["style"])
                frames.append(frame_str)
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
