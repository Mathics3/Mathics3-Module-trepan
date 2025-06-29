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

import types
from typing import Union
from trepan.lib.format import (
    Filename,
    LineNumber,
    format_token,
)
from mathics_scanner.location import MATHICS3_PATHS, SourceRange
from pymathics.trepan.lib.format import pygments_format

def format_as_file_line(loc: Union[SourceRange, types.MethodType]) -> str:
    """
    Given Location ``loc`` return a string representation of that using
    the gdb-like filename line format
    """
    if isinstance(loc, types.MethodType):
        func = loc.__func__
        # doc = func.__doc__
        code = func.__code__
        filename = {code.co_filename}
        line_number = code.co_firstlineno
        return "(%s:%s): <module>" % (filename, line_number)

    filename = MATHICS3_PATHS[loc.container]
    return "(%s:%s): <module>" % (filename, loc.start_line)

def format_location(style: str, loc: Union[SourceRange, types.MethodType]) -> str:
    """
    Given Location ``loc`` return a string representation formatting
    the line and columns.
    """
    if isinstance(loc, types.MethodType):
        func = loc.__func__
        doc = func.__doc__
        code = func.__code__
        formatted_doc = "" if doc is None else pygments_format(doc, style)
        filename = {code.co_filename}
        line_number = code.co_firstlineno
        return "%s %s at line %s" % (
            formatted_doc,
            format_token(Filename, filename, style=style),
            format_token(LineNumber, str(line_number), style=style),
            )

    filename = MATHICS3_PATHS[loc.container]
    if loc.start_line == loc.end_line:
        return "%s at line %s, columns %s-%s" % (
            format_token(Filename, filename, style=style),
            format_token(LineNumber, str(loc.start_line), style=style),
            format_token(LineNumber, str(loc.start_pos), style=style),
            format_token(LineNumber, str(loc.end_pos), style=style),
        )
    else:
        return "%s at line %s, column %s - line %s, column %s" % (
            format_token(Filename, filename, style=style),
            format_token(LineNumber, str(loc.start_line), style=style),
            format_token(LineNumber, str(loc.start_pos), style=style),
            format_token(LineNumber, str(loc.endt_line), style=style),
            format_token(LineNumber, str(loc.end_pos), style=style),
            )
