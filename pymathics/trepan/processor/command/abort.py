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
import ctypes
import threading

from mathics.core.interrupt import AbortInterrupt
from pymathics.trepan.lib.exception import DebuggerQuitException

# Our local modules
from trepan.processor.command.base_cmd import DebuggerCommand


def ctype_async_raise(thread_obj, exception):
    found = False
    target_tid = 0
    for tid, tobj in threading._active.items():
        if tobj is thread_obj:
            found = True
            target_tid = tid
            break

    if not found:
        raise ValueError("Invalid thread object")

    ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        target_tid, ctypes.py_object(exception)
    )
    # ref: http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
    if ret == 0:
        raise DebuggerQuitException
    elif ret > 1:
        # Huh? Why would we notify more than one threads?
        # Because we punch a hole into C level interpreter.
        # So it is better to clean up the mess.
        ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class AbortCommand(DebuggerCommand):
    """**abort**

    Abort the computation being interrupted set the final computation to $Aborted.

    Similar to Mathics3 command Abort[]


    See also:
    ---------

    See `continue` `exit` or `kill` for more forceful termination commands.

    `run` and `restart` restart the debugged program."""

    aliases = ("a", "abort")
    category = "support"
    max_args = 0
    short_help = "Abort computation"

    DebuggerCommand.setup(locals(), category="support", max_args=0)

    def nothread_quit(self, arg):
        """quit command when there's just one thread."""

        self.debugger.core.stop()
        self.debugger.core.execution_status = "Abort command"
        raise AbortInterrupt

    def threaded_quit(self, arg):
        """quit command when several threads are involved."""
        threading_list = threading.enumerate()
        mythread = threading.current_thread()
        for t in threading_list:
            if t != mythread:
                ctype_async_raise(t, AbortInterrupt)
                pass
            pass
        raise AbortInterrupt

    def run(self, args):
        threading_list = threading.enumerate()
        if (
            len(threading_list) == 1 or self.debugger.from_ipython
        ) and threading_list[0].name == "MainThread":
            # We are in a main thread and either there is one thread or
            # we or are in ipython, so that's safe to quit.
            return self.nothread_quit(args)
        else:
            return self.threaded_quit(args)
        return


if __name__ == "__main__":
    from pymathics.trepan.lib.repl import DebugREPL

    d = DebugREPL()
    cp = d.core.processor
    command = AbortCommand(cp)
    try:
        command.run(["abort"])
    except AbortInterrupt:
        print("A got an 'Abort' a exception. Now trying with a prompt.")
        pass
    try:
        command.run(["quit"])
    except AbortInterrupt:
        print("A got an 'Abort' a exception. Ok, be that way - I'm going home.")
        pass
    else:
        print("quit not confirmed; end of testing.")
    pass
