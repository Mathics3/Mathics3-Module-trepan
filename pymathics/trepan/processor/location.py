from typing import Tuple, Union
from types import MethodType

from trepan.lib.format import (
    Filename,
    LineNumber,
    format_token,
)

from mathics_scanner.location import MATHICS3_PATHS, SourceRange
from pymathics.trepan.lib.format import pygments_format

def format_location(proc_obj, loc: Union[SourceRange, MethodType]) -> str:
    """
    Given Location ``loc`` return a string representation of that
    """
    style=proc_obj.settings("style")
    if isinstance(loc, MethodType):
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
        # return "%s at line %s:%s-%s" % (
            # format_token(Filename, filename, style=style),
            # format_token(LineNumber, str(loc.start_line), style=style),
            # format_token(LineNumber, str(loc.start_pos), style=style),
            # format_token(LineNumber, str(loc.end_pos), style=style),
        return "(%s:%s): <module>" % (filename, loc.start_line)
    else:
        return "%s at line %s:%s-%s-%s" % (
            format_token(Filename, filename, style=style),
            format_token(LineNumber, str(loc.start_line), style=style),
            format_token(LineNumber, str(loc.start_pos), style=style),
            format_token(LineNumber, str(loc.endt_line), style=style),
            format_token(LineNumber, str(loc.end_pos), style=style),
            )
