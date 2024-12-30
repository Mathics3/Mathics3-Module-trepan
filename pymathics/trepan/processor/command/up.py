# -*- coding: utf-8 -*-
#   Copyright (C) 2024 Rocky Bernstein
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

from pymathics.trepan.processor.command.base_cmd import DebuggerCommand
from pymathics.trepan.processor.frame import FrameType, adjust_frame, frame_complete
from pymathics.trepan.processor.command.frame import frame_parser

class UpCommand(DebuggerCommand):
    """**up** [options] [*count*]

    *options* are:

       -h | --help    - give this help
       -b | --builtin - show Mathics3 builtin methods
       -e | --expr    - show Mathics3 Expressions

        Move the current frame up in the stack trace (to an older frame). 0 is
        the most recent frame. If no count is given, move up 1.

    **Examples:**

       up       # Move one frame older
       up 1     # Same as above
       up B:1   # Move to the next-older builtin frame
       up b:1   # Same as above.
       up -b 1  # Same as above
       up e:1   # Move to the next-newer builtin frame

    See also:
    ---------

    `down` and `frame`."""
    signum = -1  # This is what distinguishes us from "down"

    DebuggerCommand.setup(locals(), category="stack", need_stack=True, max_args=2)

    # TODO: adjust for options
    def complete(self, prefix):
        proc_obj = self.proc
        return frame_complete(proc_obj, prefix, self.signum)

    def run(self, args):

        opts, rest_args = frame_parser.parse_args(args[1:])

        if len(rest_args) > 0:
            if rest_args[0].lower().startswith("b:"):
                opts.builtin = True
                rest_args[0] = rest_args[0][2:]
            elif rest_args[0].lower().startswith("e:"):
                opts.expression = True
                rest_args[0] = rest_args[0][2:]

        frame_type = FrameType.python
        if opts.builtin:
            frame_type = FrameType.builtin
        elif opts.expression:
            frame_type = FrameType.expression

        if len(rest_args) == 0:
            amount = 1
        else:
            amount = self.proc.get_an_int(
                rest_args[0],
                f"The 'up command requires a count. Got: {rest_args[0]}"
                )
            if amount is None:
                return

        adjust_frame(self.proc, amount * self.signum, False,
                     frame_type)
        return False


if __name__ == "__main__":
    from pymathics.trepan.lib.repl import DebugREPL
    from trepan.processor.cmdproc import get_stack

    d = DebugREPL()
    cp = d.core.processor
    command = UpCommand(cp)
    command.run(["up"])

    def nest_me(command_proc, my_command, i):
        import inspect

        if i > 1:
            command_proc.curframe = inspect.currentframe()
            command_proc.stack, command_proc.curindex = get_stack(
                command_proc.curframe, None, None, command_proc
            )
            my_command.run(["up"])
            print("-" * 10)
            my_command.run(["up", "1"])
            print("-" * 10)
            my_command.run(["up", "-e", "1"])
            print("-" * 10)
            my_command.run(["up", "3"])
            print("-" * 10)
        else:
            nest_me(command_proc, my_command, i + 1)
        return

    cp.forget()
    nest_me(cp, command, 1)
    pass
