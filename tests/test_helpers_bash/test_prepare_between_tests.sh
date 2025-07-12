#! /bin/bash

# Prepare tests.
if [ -f "${VIM_DISPOSABLE_PYFILE}" ]; then
    rm "${VIM_DISPOSABLE_PYFILE}"
fi
VIM_DISPOSABLE_PYFILE="/tmp/pymode.tmpfile.$(date +%s).py"
export VIM_DISPOSABLE_PYFILE

touch "${VIM_DISPOSABLE_PYFILE}"
# vim: set fileformat=unix filetype=sh wrap tw=0 :