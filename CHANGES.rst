CHANGES
=======
08/30/2025

Support Python 3.13. Remove support for Python 3.8 and Python 3.9.
Revise for new location API and 9.0.0 release.

* added debugger commands:
  - ``abort``
  - ``info program``
  - ``set return``
  - ``quit``
* Improve ``Element`` printing
  - Handle Slot[x] -> #x
  - add unary precedence
* Add ``DebugEvaluation[]`` Builtin Function
* ``TraceEvaluation[]`` improvements:
  - Returning ``x <- tuple(y)`` becomes ``Replacing x -> y``
  - Show locations on ``TraceEvaluation[]``
* Show Mathics3 source location sometimes when $TrackLocaitons is set.
* respect ``TREPAN_PYGMENTS_STYLE`` for setting pygments style


=======
01/27/2025

1.0.1

Revise for API changes in the 8.0.0 release.

-------

01/20/2025

1.0.0

First public release. Add Builtin Functions:

* ``DebugActivate``
* ``Debugger``, and
* ``TraceActivate``

``TraceEvaluation[]`` is overwritten to provide better trace output.
