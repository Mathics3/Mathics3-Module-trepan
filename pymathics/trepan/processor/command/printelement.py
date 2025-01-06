# -*- coding: utf-8 -*-
#  Copyright (C) 2024 Rocky Bernstein
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from getopt import getopt, GetoptError

from mathics.core.element import BaseElement
from mathics.core.pattern import AtomPattern, ExpressionPattern
from mathics.core.rules import FunctionApplyRule, Rule
from pymathics.trepan.processor.command.base_cmd import DebuggerCommand
from pymathics.trepan.lib.format import format_element, pygments_format

class PrintElementCommand(DebuggerCommand):
    """**printelement** [-p] [*Mathics3 element*]

    Print a Mathics3 *expression* formatted nicely, as opposed to
    its Python-object way.

    If option -p is supplied, we loosen what is acceptable as a Mathics3 element;
    we Mathics3 elements to be wrapped in lists, dictionaries, and tuples.
    """

    from importlib import reload
    import pymathics
    reload(pymathics.trepan.lib.format)

    aliases = ("print-element", "pexp", "pe")
    short_help = "Print a Mathics3 Expression nicely"
    DebuggerCommand.setup(locals(), category="running", max_args=2, need_stack=True)

    def run(self, args):
        try:
            opts, args = getopt(args[1:], "hp", "help".split())
        except GetoptError as err:
            # print help information and exit:
            print(str(err))  # will print something like "option -a not recognized"
            return

        allow_python = False
        for o, _ in opts:
            if o in ("-h", "--help"):
                self.proc.commands["help"].run(["help", "printelement"])
                return
            elif o in ("-p",):
                allow_python = True
            else:
                self.errmsg(f"unhandled option '{o}'")
            pass

        text = self.proc.current_command[len(self.proc.cmd_name) :].lstrip()
        if text.startswith("-p"):
            text = text[2:]
        text = text.strip()
        try:
            value = self.proc.eval(text)
        except Exception:
            return

        if not allow_python or not isinstance(value, (dict, list, tuple)):
            if not isinstance(value, (AtomPattern, BaseElement,
                                      ExpressionPattern, FunctionApplyRule, Rule)):
                self.errmsg(f"text: {text} does not evaluate to a type I know about; is {type(value)}")
                if isinstance(value, (dict, list, tuple)):
                    self.msg("Try adding option -p?")
                return

        mathics_str = format_element(value, allow_python=allow_python,
                                     use_operator_form=True)
        self.msg(pygments_format(mathics_str, self.settings["style"]))
    pass


if __name__ == "__main__":
    pass
