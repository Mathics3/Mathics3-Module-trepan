#  Copyright (C) 2024-2025 Rocky Bernstein
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
# import sys

import subprocess
from mathics.core.evaluation import Evaluation

from mathics.__main__ import TerminalOutput, TerminalShell, show_echo

# Our local modules
from pymathics.trepan.processor.command.base_cmd import DebuggerCommand
from pymathics.trepan.processor.frame import find_builtin

# FIXME: pick up from mathics.core.main or some place like that
def eval_loop(shell):
    while True:
        try:
            evaluation = Evaluation(shell.definitions, output=TerminalOutput(shell))
            query, source_code = evaluation.parse_feeder_returning_code(shell)
            show_echo(source_code, evaluation)
            if len(source_code) and source_code[0] == "!":
                subprocess.run(source_code[1:], shell=True)
                shell.definitions.increment_line_no(1)
                continue
            if query is None:
                continue
            result = evaluation.evaluate(query)
            if result is not None:
                shell.print_result(result, strict_wl_output=False)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt - returning to Mathics3 Debug... ")
            break
        except EOFError:
            print("\nReturning to Mathics3 Debug...\n")
            break
        except SystemExit:
            print("\n\nGoodbye!\n")
            # raise to pass the error code on, e.g. Quit[1]
            raise
        finally:
            shell.reset_lineno()



class Mathics3Command(DebuggerCommand):
    """**mathics3**

    Fork a new Mathics3 session using the existing definitions
    """

    aliases = ("mathics", "Mathics3")
    short_help = "Run Python as a command subshell"

    DebuggerCommand.setup(locals(), category="data", max_args=0, min_args=0)

    def run(self, args):

        # Find an eval() frame, arom that find a evaluation object.
        # And from that get a definitions object.

        frame = find_builtin(self.proc.curframe)
        if frame is None:
            self.errmsg("Cannot find an eval frame to start with")
            return

        evaluation = frame.f_locals.get("evaluation")
        if evaluation is None:
            self.errmsg("Cannot find evaluation object from eval frame")
            return

        if not hasattr(evaluation, "definitions"):
            self.errmsg("Cannot find definitions in evaluation object")
            return

        definitions = evaluation.definitions
        shell = TerminalShell(
            definitions,
            "NoColor",
            want_readline=True,
            want_completion=True,
            autoload=False,
            in_prefix="Debug In",
            out_prefix="Debug Out"
        )
        eval_loop(shell)


    pass


# if __name__ == "__main__":
#     from pymathics.trepan.lib.repl import DebugREPL

#     d = DebugREPL()
#     command = Mathics3Command(d.core.processor)
#     command.proc.frame = sys._getframe()
#     command.proc.setup()
#     if len(sys.argv) > 1:
#         print("Type Python commands and exit to quit.")
#         print(sys.argv[1])
#         if sys.argv[1] == "-d":
#             print(command.run(["python", "-d"]))
#         else:
#             print(command.run(["python"]))
#             pass
#         pass
#     pass
