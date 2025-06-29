# -*- coding: utf-8 -*-
#   Copyright (C) 2025 Rocky Bernstein <rocky@gnu.org>
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

import inspect

from pymathics.trepan.lib.format import pygments_format
from trepan.processor.command.base_subcmd import DebuggerSubcommand


class InfoReturn(DebuggerSubcommand):
    """**info return**

    Show the value that will be returned back to Mathics3 when the
    debugger leaves or continues.
    """

    def run(self, args):
        style = self.debugger.settings["style"]
        return_str = str(self.proc.return_value)
        self.msg(f"Value set to return: {pygments_format(return_str, style)}")

        if self.proc.event != "evaluate-result" and self.proc.return_value is None:
            self.msg("Note: the None value indicates no change in expression value on debugger exit.")
        return


if __name__ == "__main__":
    from pymathics.trepan.processor.command import mock, info as Minfo

    d, cp = mock.dbg_setup()
    i = Minfo.InfoCommand(cp)
    sub = InfoReturn(i)
    pass
