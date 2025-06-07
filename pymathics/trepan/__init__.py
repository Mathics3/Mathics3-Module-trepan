"""
Mathics3 Debugger

In this Mathics3 module, we have a command-line debugger for Mathics3. With it, you can inspect Mathic3 objects \
at both the Mathics3 and Python level.

This debugger is based on the gdb-like <i>trepan</i> series of debuggers, <url>:trepan3k:https://pypi.org/project/trepan3k/</url> \
in particular.
"""

from pymathics.trepan.__main__ import DebugActivate, Debugger, TraceActivate
from pymathics.trepan.debug_evaluation import DebugEvaluation
from pymathics.trepan.version import __version__

pymathics_version_data = {
    "author": "The Mathics3 Team",
    "version": __version__,
    "name": "Debugger",
    "requires": [],
}


# These are the publicly exported names
__all__ = [
    "DebugActivate",
    "DebugEvaluation",
    "Debugger",
    "TraceActivate",
    "pymathics_version_data",
]
