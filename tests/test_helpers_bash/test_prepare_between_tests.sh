#! /bin/bash

# Prepare tests.
set +e
rm $VIM_DISPOSABLE_PYFILE 2&>/dev/null
set -e
touch $VIM_DISPOSABLE_PYFILE

# vim: set fileformat=unix filetype=sh wrap tw=0 :
