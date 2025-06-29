# -*- coding: utf-8 -*-

#   Copyright (C) 2024 Rocky Bernstein <rocky@gnu.org>
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
""" Functions for working with Python frames"""

import inspect
import os.path as osp

from typing import Optional, Tuple
from trepan.lib.format import (
    Arrow,
    Function,
    format_token,
)

from trepan.lib.stack import (
    format_function_name,
    format_return_and_location,
    get_call_function_name,
    is_eval_or_exec_stmt,
)
from mathics.core.builtin import Builtin
from mathics.core.element import BaseElement
from mathics.core.evaluation import Evaluation
from mathics.core.expression import Expression
from mathics.core.pattern import ExpressionPattern
from pymathics.trepan.lib.format import format_element, pygments_format


def count_frames(frame, count_start=0):
    """Return a count of the number of frames"""
    count = -count_start
    while frame:
        count += 1
        frame = frame.f_back
    return count


def format_frame_self_arg(
    frame, args, debugger, style: str
) -> Optional[str]:
    """If there is a "self" argument and it is is a Mathics3 kind of
    object, format that separately as its Mathics3 representation (as
    opposed to how it looks in Python).
    """
    self_arg = frame.f_locals.get("self", None)
    if self_arg is None:
        return None
    if (
        len(args) > 0
        and args[0] == "self"
        and isinstance(self_arg, (BaseElement, ExpressionPattern))
    ):
        self_arg_mathics_formatted = format_element(self_arg)
    else:
        self_arg_mathics_formatted = None

    return self_arg_mathics_formatted


def format_function_and_parameters(frame, debugger, style: str) -> Tuple[bool, str]:
    """
    format the function found in frame along with its paramter. This is passed back as a string.
    The style to used is given by ``style``; style "none" means do not style.
    We also pass back wither the frame function is a module-level function.
    """

    funcname, s = format_function_name(frame, style)
    args, varargs, varkw, local_vars = inspect.getargvalues(frame)
    if "<module>" == funcname and (
        [],
        None,
        None,
    ) == (
        args,
        varargs,
        varkw,
    ):
        is_module = True
        if (func_name := is_eval_or_exec_stmt(frame)):
            s += f" {format_token(Function, func_name, style=style)}(...)"
        else:
            # FIXME: package the below as a function in trepan3k
            func_name = get_call_function_name(frame)
            if func_name:
                if func_name:
                    s += f" {format_token(Function, func_name, style=style)}({...})"
            pass
    else:
        is_module = False
        self_arg_mathics_formatted = format_frame_self_arg(frame, args, debugger, style)

        if self_arg_mathics_formatted is not None:
            args = args[1:]

        if len(args) > 0 and args[-1] == "evaluation" and isinstance(local_vars["evaluation"], Evaluation):
            # Simiplify: We don't need to show the evaluation parameter along with
            # its type and object address.
            args = args[:-1]

        try:
            params = inspect.formatargvalues(args, varargs, varkw, local_vars)
        except Exception:
            pass
        else:
            maxargstrsize = debugger.settings["maxargstrsize"]
            param_len = len(params)
            if self_arg_mathics_formatted is not None:
                if len(self_arg_mathics_formatted) > maxargstrsize:
                    self_arg_mathics_formatted = (
                        f"{self_arg_mathics_formatted[0:maxargstrsize]}...)"
                    )
                if param_len > 0:
                    if params[0] == "(":
                        params = params[1:]
                    # We have to do this before pygments_format so that it appears before a \n'
                    self_arg_mathics_formatted += ","
                first_param = "(" + pygments_format(
                    self_arg_mathics_formatted, style=style
                )
                if param_len > 0:
                    first_param += "\t"
                    pass
            else:
                first_param = ""

            # Tack on first argument if there is one
            if len(params) >= maxargstrsize:
                params = f"{params[0:maxargstrsize]}...)"

            params = f"{first_param}{params}"
            s += params
        pass

    return is_module, s


def format_eval_builtin_fn(frame, style: str) -> str:
    """
    Extract and format Mathics Builtin function information
    from ``frame`` and return that as a string.
    ``frame`` is assumed to be a Python frame
    for which is_builtin_eval(frame) is True.
    """
    self_obj = frame.f_locals.get("self")
    builtin_name = self_obj.__class__.__name__

    eval_name = frame.f_code.co_name
    if hasattr(self_obj, eval_name):
        docstring = getattr(self_obj, eval_name).__doc__
        docstring = docstring.replace("%(name)s", builtin_name)
        args_pattern = (
            docstring[len(builtin_name) + 1 : -1]
            if docstring.startswith(builtin_name)
            else ""
        )
    else:
        args_pattern = ""

    call_string = f"{builtin_name}[{args_pattern}]"
    formatted_call_string = pygments_format(call_string, style)
    return formatted_call_string


def format_stack_entry(
    dbg_obj, frame_lineno, lprefix=": ", include_location=True, style="none"
) -> str:
    """Format and return a stack entry gdb-style.
    Note: lprefix is not used. It is kept for compatibility.
    """
    frame, line_number = frame_lineno

    if is_builtin_eval_fn(frame):
        s = format_eval_builtin_fn(frame, style=style)
        s += "    "
        is_module = False
    else:
        is_module, s = format_function_and_parameters(frame, dbg_obj, style)
        args, varargs, varkw, local_vars = inspect.getargvalues(frame)

        # Note: ddd can't handle wrapped stack entries (yet).
        # The 35 is hoaky though. FIXME.
        if len(s) >= 35:
            s += "\n    "

    s += format_return_and_location(
        frame, line_number, dbg_obj, is_module, include_location, style
    )
    return s


def is_builtin_eval_fn(frame) -> bool:
    """
    Return True if frame is the frame for a an eval() function of a
    Mathics3 Builtin function.

    We make the check based on whether the function name starts with "eval",
    has a "self" parameter and the class that self is an instance of the Builtin
    class.
    """
    if not inspect.isframe(frame):
        return False
    if not frame.f_code.co_name.startswith("eval"):
        return False
    self_obj = frame.f_locals.get("self")
    return isinstance(self_obj, Builtin)


def print_expression_stack(proc_obj, count: int, style="none"):
    """
    Display the Python call stack but filtered so that we show only expresions.
    """
    j = 0
    intf = proc_obj.intf[-1]
    n = len(proc_obj.stack)
    for i in range(n):
        frame_lineno = proc_obj.stack[len(proc_obj.stack) - i - 1]
        frame = frame_lineno[0]
        self_obj = frame.f_locals.get("self", None)
        if isinstance(self_obj, Expression):
            if frame is proc_obj.curframe:
                intf.msg_nocr(format_token(Arrow, "E>", style=style))
            else:
                intf.msg_nocr("E:")
            stack_nums = f"{j} ({i})"
            intf.msg(f"{stack_nums} {frame.f_code.co_qualname} {self_obj.__class__}")
            intf.msg(
                " " * (4 + len(stack_nums))
                + format_stack_entry(proc_obj.debugger, frame_lineno, style=style)
            )
            j += 1
            if j >= count:
                break


def print_builtin_stack(proc_obj, count: int, style="none"):
    """
    Display the Python call stack but filtered so that we Builtin calls.
    """
    j = 0
    intf = proc_obj.intf[-1]
    n = len(proc_obj.stack)
    for i in range(n):
        frame_lineno = proc_obj.stack[len(proc_obj.stack) - i - 1]
        frame, line_number = frame_lineno
        if is_builtin_eval_fn(frame):
            if frame is proc_obj.curframe:
                intf.msg_nocr(format_token(Arrow, "B>", style=style))
            else:
                intf.msg_nocr("B:")
            stack_nums = f"{j} ({i})"
            intf.msg(f"{stack_nums} {format_eval_builtin_fn(frame, style=style)}")
            intf.msg(
                " " * (4 + len(stack_nums))
                + format_return_and_location(
                    frame, line_number, proc_obj.debugger, False, True, style
                     ))
            j += 1
            if j >= count:
                break


def print_stack_entry(proc_obj, i_stack: int, style="none", opts={}):
    frame_lineno = proc_obj.stack[len(proc_obj.stack) - i_stack - 1]
    frame, _ = frame_lineno
    intf = proc_obj.intf[-1]
    if frame is proc_obj.curframe:
        intf.msg_nocr(format_token(Arrow, "->", style=style))
    else:
        intf.msg_nocr("##")
    intf.msg(
        f"{i_stack} {format_stack_entry(proc_obj.debugger, frame_lineno, style=style)}"
    )


def print_stack_trace(proc_obj, count=None, style="none", opts={}):
    "Print ``count`` entries of the stack trace"
    if count is None:
        n = len(proc_obj.stack)
    else:
        n = min(len(proc_obj.stack), count)
    try:
        if opts["builtin"]:
            print_builtin_stack(proc_obj, n, style=style)
        elif opts["expression"]:
            print_expression_stack(proc_obj, n, style=style)
        else:
            for i in range(n):
                print_stack_entry(proc_obj, i, style=style, opts=opts)
    except KeyboardInterrupt:
        pass
    return


def print_dict(s, obj, title):
    if hasattr(obj, "__dict__"):
        d = obj.__dict__
        if isinstance(d, dict):
            keys = list(d.keys())
            if len(keys) == 0:
                s += f"\n  No {title}"
            else:
                s += f"\n  {title}:\n"
            keys.sort()
            for key in keys:
                s += f"    '{key}':\t{d[key]}\n"
                pass
            pass
        pass
    return s


def eval_print_obj(arg, frame, format=None, short=False):
    """Return a string representation of an object"""
    try:
        if not frame:
            # ?? Should we have set up a dummy globals
            # to have persistence?
            val = eval(arg, None, None)
        else:
            val = eval(arg, frame.f_globals, frame.f_locals)
            pass
    except Exception:
        return 'No symbol "' + arg + '" in current context.'

    return print_obj(arg, val, format, short)


def print_obj(arg, val, format=None, short=False):
    """Return a string representation of an object"""
    what = arg
    if format:
        what = format + " " + arg
        val = printf(val, format)
        pass
    s = f"{what} = {val}"
    if not short:
        s += f"\n  type = {type(val)}"
        # Try to list the members of a class.
        # Not sure if this is correct or the
        # best way to do.
        s = print_dict(s, val, "object variables")
        if hasattr(val, "__class__"):
            s = print_dict(s, val.__class__, "class variables")
            pass
        pass
    return s


# Demo stuff above
if __name__ == "__main__":

    class MockDebuggerCore:
        def canonic_filename(self, frame):
            return frame.f_code.co_filename

        def filename(self, name):
            return name

        pass

    class MockDebugger:
        def __init__(self):
            self.core = MockDebuggerCore()
            self.settings = {"maxargstrsize": 80}
            pass

        pass

    frame = inspect.currentframe()
    pyc_file = osp.join(
        osp.dirname(__file__), "__pycache__", osp.basename(__file__)[:-3] + ".pyc"
    )

    m = MockDebugger()
    print(
        format_stack_entry(
            m,
            (
                frame,
                10,
            ),
        )
    )
    # print(format_stack_entry(m, (frame, 10,), color="dark"))
    # print("frame count: %d" % count_frames(frame))
    # print("frame count: %d" % count_frames(frame.f_back))
    # print("frame count: %d" % count_frames(frame, 1))
    # print("def statement: x=5?: %s" % repr(is_def_stmt("x=5", frame)))
    # # Not a "def" statement because frame is wrong spot
    # print(is_def_stmt("def foo():", frame))

    # def sqr(x):
    #     x * x

    # def fn(x):
    #     frame = inspect.currentframe()
    #     print(get_call_function_name(frame))
    #     return

    # print("=" * 30)
    # eval("fn(5)")
    # print("=" * 30)
    # print(print_obj("fn", fn))
    # print("=" * 30)
    # print(print_obj("len", len))
    # print("=" * 30)
    # print(print_obj("MockDebugger", MockDebugger))
    pass
