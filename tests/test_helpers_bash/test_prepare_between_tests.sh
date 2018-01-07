#! /bin/bash

# Prepare tests.
set +e
rm $VIM_DISPOSABLE_PYFILE
export VIM_DISPOSABLE_PYFILE=`mktemp /tmp/pymode.tmpfile.XXXXXXXXXX.py`
set -e
touch $VIM_DISPOSABLE_PYFILE

# vim: set fileformat=unix filetype=sh wrap tw=0 :
