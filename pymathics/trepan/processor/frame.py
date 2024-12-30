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
#
# Call-frame-oriented helper function for Processor. Put here so we
# can use this in a couple of processors.

from enum import Enum

from mathics.core.expression import Expression
from trepan.lib.complete import complete_token
from trepan.processor.frame import adjust_frame as trepan_adjust_frame
from trepan.processor.frame import frame_low_high

from pymathics.trepan.lib.stack import is_builtin_eval_fn

FrameTypeNames = ("expression", "builtin", "python")
FrameType = Enum("FrameType", FrameTypeNames)


def adjust_frame(proc_obj, count: int, is_absolute_pos: bool, frame_type: FrameType):
    """Adjust stack frame by pos positions. If is_absolute_pos then
    pos is an absolute number. Otherwise it is a relative number.

    A negative number indexes from the other end."""
    if not proc_obj.curframe:
        proc_obj.errmsg("No stack.")
        return

    if frame_type == FrameType.python:
        if is_absolute_pos:
            adjusted_pos = count
        else:
            adjusted_pos = len(proc_obj.stack) - proc_obj.curindex -1
            if count > adjusted_pos:
                proc_obj.errmsg("Adjusting would put us beyond the oldest frame.")
                return
            adjusted_pos -= count
    elif frame_type == FrameType.expression:
        stack_len = len(proc_obj.stack)
        my_range = range(stack_len - 1, -1, -1)
        for i in my_range:
            frame_lineno = proc_obj.stack[i]
            frame = frame_lineno[0]
            self_obj = frame.f_locals.get("self", None)
            if isinstance(self_obj, Expression):
                if count == 0:
                    adjusted_pos = stack_len - i - 1
                    break
                count -= 1
            pass
        else:
            direction = "newest" if count < 0 else "oldest"
            proc_obj.errmsg(f"Adjusting would put us beyond the {direction} "
                            "frame.")
    elif frame_type == FrameType.builtin:
        stack_len = len(proc_obj.stack)
        my_range = range(stack_len - 1, -1, -1)
        for i in my_range:
            frame_lineno = proc_obj.stack[i]
            frame = frame_lineno[0]
            if is_builtin_eval_fn(frame):
                if count == 0:
                    adjusted_pos = stack_len - i - 1
                    break
                count -= 1
            pass
        else:
            direction = "newest" if count < 0 else "oldest"
            proc_obj.errmsg(f"Adjusting would put us beyond the {direction} "
                            "frame.")
            return
    else:
        adjusted_pos = count

    trepan_adjust_frame(proc_obj, adjusted_pos, is_absolute_pos=True)
    return

def find_builtin(frame):
    while frame is not None:
        if is_builtin_eval_fn(frame):
            return frame
        frame = frame.f_back
    return None


# TODO: add options
def frame_complete(proc_obj, prefix, direction):
    low, high = frame_low_high(proc_obj, direction)
    ary = [str(low + i) for i in range(high - low + 1)]
    return complete_token(ary, prefix)


def frame_num(proc_obj, pos: int, frame_type) -> int:
    if frame_type == FrameType.python:
        return len(proc_obj.stack) - pos - 1
    elif frame_type == FrameType.expression:
        n = len(proc_obj.stack) - 1
        for adjusted_pos in range(n, 0, -1):
            frame, _ = proc_obj.stack[adjusted_pos]
            self_obj = frame.f_locals.get("self", None)
            if isinstance(self_obj, Expression):
                pos -= 1
                if pos == 0:
                    return adjusted_pos
        proc_obj.errmsg("Adjusting would put us beyond the newest frame.")
