#!/bin/bash
PACKAGE=Mathics3-Module-trepan

# FIXME put some of the below in a common routine
function finish {
  if [[ -n "$mathics3_trepan_owd" ]] then
     cd $mathics3_trepan_owd
  fi
}

cd $(dirname ${BASH_SOURCE[0]})
mathics3_trepan_owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-versions ; then
    exit $?
fi


cd ..
source pymathics/trepan/version.py
echo $__version__

pyversion=3.13.5
if ! pyenv local $pyversion ; then
    exit $?
fi

pip wheel --wheel-dir=dist .
python -m build --sdist
finish
