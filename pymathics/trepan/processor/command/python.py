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
import sys
from typing import Callable

from trepan.interfaces.server import ServerInterface

# Our local modules
from pymathics.trepan.processor.command.base_cmd import DebuggerCommand
from trepan.processor.command.python import interact

class PythonCommand(DebuggerCommand):
    """**python** [**-d**]

    Run Python as a command subshell. The *sys.ps1* prompt will be set to
    `Mathics3 Debug >>> `.

    If *-d* is passed, you can access debugger state via local variable *debugger*.

    """

    aliases = ("py", "interact", "shell")
    short_help = "Run Python as a command subshell"

    DebuggerCommand.setup(locals(), category="data", max_args=1)

    def dbgr(self, string):
        """Invoke a debugger command from inside a python shell called inside
        the debugger.
        """
        self.proc.cmd_queue.append(string)
        self.proc.process_command()
        return

    def run(self, args):
        # See if python's code module is around

        # Python does its own history thing.
        # Make sure it doesn't damage ours.
        intf = self.debugger.intf[-1]
        if isinstance(intf, ServerInterface):
            self.errmsg("Can't run an interactive shell on a remote session")
            return

        have_line_edit = self.debugger.intf[-1].input.line_edit
        if have_line_edit:
            try:
                self.proc.write_history_file()
            except IOError:
                pass
            pass

        banner_tmpl = """Mathics3 Debugger python shell%s
Use dbgr(*string*) to issue debugger command: *string*"""

        debug = len(args) > 1 and args[1] == "-d"
        if debug:
            banner_tmpl += "\nVariable 'debugger' contains a Mathics3 debugger object."
            pass

        my_locals = {}
        my_globals = None
        proc = self.proc
        if proc.curframe:
            my_globals = proc.curframe.f_globals
            if proc.curframe.f_locals:
                my_locals = proc.curframe.f_locals
                pass
            pass

        # Give python and the user a way to get access to the debugger.
        if debug:
            my_locals["debugger"] = self.debugger
        my_locals["dbgr"] = self.dbgr

        # Change from debugger completion to python completion
        try:
            import readline
        except ImportError:
            pass
        else:
            readline.parse_and_bind("tab: complete")

        sys.ps1 = "Mathics3 Debug >>> "
        old_sys_excepthook = sys.excepthook
        try:
            sys.excepthook = None
            if len(my_locals):
                interact(
                    banner=(banner_tmpl % " with locals"),
                    my_locals=my_locals,
                    my_globals=my_globals,
                )
            else:
                interact(banner=(banner_tmpl % ""))
                pass
        finally:
            sys.excepthook = old_sys_excepthook

        # restore completion and our history if we can do so.
        if hasattr(proc.intf[-1], "complete") and isinstance(proc.intf[-1], Callable):
            try:
                from readline import parse_and_bind, set_completer

                parse_and_bind("tab: complete")
                set_completer(proc.intf[-1].complete)
            except ImportError:
                pass
            pass

        if have_line_edit:
            proc.read_history_file()
            pass
        return

    pass


if __name__ == "__main__":
    from pymathics.trepan.lib.repl import DebugREPL

    d = DebugREPL()
    command = PythonCommand(d.core.processor)
    command.proc.frame = sys._getframe()
    command.proc.setup()
    if len(sys.argv) > 1:
        print("Type Python commands and exit to quit.")
        print(sys.argv[1])
        if sys.argv[1] == "-d":
            print(command.run(["python", "-d"]))
        else:
            print(command.run(["python"]))
            pass
        pass
    pass
