# -*- coding: utf-8 -*-
#   Copyright (C) 2024-2025 Rocky Bernstein <rocky@gnu.org>
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

# Our local modules
from trepan.processor.command.base_subcmd import DebuggerSubcommand
from pymathics.trepan.lib.format import format_element, pygments_format
from pymathics.trepan.lib.location import format_location
from pymathics.trepan.lib.stack import print_stack_trace


class InfoProgram(DebuggerSubcommand):
    """**info program**

    Execution status of the program. Listed are:

    * Most recent Mathics3 expression

    * Reason the program is stopped.

    """

    min_abbrev = 2  # Need at least "info pr"
    max_args = 0
    need_stack = True
    short_help = "Execution status of the program"

    def run(self, args):
        """Execution status of the program."""
        proc = self.proc
        event = proc.event
        if event:
            msg = f"Mathics3 stop via a '{event}' event."
            self.msg(msg)

        style=self.settings["style"]

        event_arg = proc.event_arg
        if isinstance(event_arg, tuple) and len(event_arg) > 0:
            event_arg = event_arg[0]
        if hasattr(event_arg, "location") and event_arg.location:
            mess = format_location(style, event_arg.location)
            self.msg(mess)
            return

        if (eval_expression := self.proc.eval_expression) is not None:
            eval_expression_str = format_element(eval_expression, allow_python=False, use_operator_form=True)
            formatted_expression = pygments_format(eval_expression_str, style=style)
            self.msg(f"Expression: {formatted_expression}")

        if self.proc.return_value is not None:
            return_str = str(self.proc.return_value)
            self.msg(f"Value set to return: {pygments_format(return_str, style)}")

        if event == "evalMethod":
            callback_arg = self.core.arg
            formatted_function = pygments_format(f"{callback_arg[0]}[]", style=style)

            self.msg(f"Built-in Function: {formatted_function}")
            # TODO get function from the target of the FunctionApplyRule if that
            # is what we have

            self.msg(f"method_function: {callback_arg[1]}")
            self.msg(f"args: {callback_arg[2]}")
            self.msg(f"kwargs: {callback_arg[3]}")
        elif event == "mpmath":
            callback_arg = self.core.arg
            formatted_function = pygments_format(f"{callback_arg[0]}()", style=style)
            self.msg(f"mpmath function: {formatted_function}")
            # self.msg(f"mpmath method: {callback_arg[1]}")
        elif event == "SymPy":
            callback_arg = self.core.arg
            formatted_function = pygments_format(f"{callback_arg[0]}()", style=style)
            self.msg(f"SymPy function: {formatted_function}")
            # self.msg(f"mpmath method: {callback_arg[1]}")


        print_stack_trace(
            self.proc,
            1,
            style=style,
            opts={"expression": True, "builtin": False},
        )
        print_stack_trace(
            self.proc,
            1,
            style=style,
            opts={"expression": True, "builtin": True},
        )
        return


if __name__ == "__main__":
    from pymathics.trepan.processor.command import mock, info as Minfo

    d, cp = mock.dbg_setup()
    i = Minfo.InfoCommand(cp)
    sub = InfoProgram(i)
    sub.run([])
