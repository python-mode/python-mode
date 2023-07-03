#! /bin/bash

# Define variables for common test scripts.

# Set variables.
VIM_DISPOSABLE_PYFILE="$(mktemp /tmp/pymode.tmpfile.XXXXXXXXXX.py)"
export VIM_DISPOSABLE_PYFILE
VIM_OUTPUT_FILE=/tmp/pymode.out
export VIM_OUTPUT_FILE
VIM_TEST_VIMRC=/tmp/pymode_vimrc
export VIM_TEST_VIMRC
VIM_TEST_PYMODECOMMANDS=/tmp/pymode_commands.txt
export VIM_TEST_PYMODECOMMANDS

# vim: set fileformat=unix filetype=sh wrap tw=0 :
