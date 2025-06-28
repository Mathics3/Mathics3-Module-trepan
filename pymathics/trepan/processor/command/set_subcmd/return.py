# -*- coding: utf-8 -*-
#   Copyright (C) 2025 Rocky Bernstein
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

from mathics.core.parser.util import parse_returning_code
from mathics_scanner.errors import SyntaxError
from mathics_scanner.location import ContainerKind
from mathics_scanner.feed import SingleLineFeeder
from trepan.processor.command.base_subcmd import DebuggerSubcommand
from pymathics.trepan.lib.format import pygments_format


class SetReturn(DebuggerSubcommand):
    """**set return** *mathics-expr*

    The the return value for a call or return expression.
    *mathics-expr* is a mathics expression for the return value.

    Examples:
    --------

        set return 1 + 5
        set return Sin[x]

    """

    def run(self, args):
        command = self.proc.current_command[len("set return ") :]

        frame = self.proc.curframe
        if frame is None:
            self.errmsg("Cannot find an eval frame to start with")
            return
        evaluation = frame.f_locals.get("evaluation", None)
        if evaluation is None:
            self.errmsg("Cannot find evaluation object from eval frame")
            return

        if not hasattr(evaluation, "definitions"):
            self.errmsg("Cannot find definitions in evaluation object")
            return

        feeder = SingleLineFeeder(command, container="<set return input>",
                                  container_kind=ContainerKind.STREAM)
        definitions = evaluation.definitions
        try:
            mathics_expr, _ = parse_returning_code(definitions, feeder)
        except SyntaxError as e:
            self.ermmsg(str(e))
            return

        if mathics_expr is None:
            return

        # Validation done. Now we can set the return value

        style = self.debugger.settings["style"]
        mathics_str = str(mathics_expr)
        old_return_str = str(self.proc.return_value)
        self.msg(f"Return value was: {pygments_format(old_return_str, style)}")
        self.msg(f"Return set to: {pygments_format(mathics_str, style)}")
        self.proc.return_value = mathics_expr
        return


if __name__ == "__main__":
    from trepan.processor.command.set_subcmd.__demo_helper__ import demo_run

    demo_run(SetReturn, ["5"])
    demo_run(SetReturn, [])
    pass
