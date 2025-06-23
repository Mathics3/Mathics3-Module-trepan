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

from mathics.core.list import ListExpression
from mathics.core.parser.util import parse_returning_code
from mathics.core.symbols import SymbolFalse, SymbolTrue
from mathics_scanner.errors import SyntaxError
from mathics_scanner.feed import SingleLineFeeder
from trepan.processor.command.base_subcmd import DebuggerSubcommand


class SetReturn(DebuggerSubcommand):
    """**set return *mathics-expr*

    The the return value for a call or return expression.
    *mathics-expr* is a mathics expression for the return value,
    True or False also needs to be given to specify whether the value is final
    or whether it might undergo another rewrite and evaluation step.

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

        feeder = SingleLineFeeder(command, filename="<set return input>")
        definitions = evaluation.definitions
        try:
            mathics_expr, _ = parse_returning_code(definitions, feeder)
        except SyntaxError as e:
            self.ermmsg(str(e))
            return

        if mathics_expr is None:
            return

        # Validation done. Now we can set the return value

        print(mathics_expr)
        self.proc.return_value = mathics_expr
        return


if __name__ == "__main__":
    from trepan.processor.command.set_subcmd.__demo_helper__ import demo_run

    demo_run(SetReturn, ["[5, True]"])
    demo_run(SetReturn, [])
    pass
