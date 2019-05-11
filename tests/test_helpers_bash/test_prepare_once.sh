#! /bin/bash

# Prepare tests.
set +e
rm $VIM_OUTPUT_FILE $VIM_TEST_VIMRC $VIM_TEST_PYMODECOMMANDS $VIM_DISPOSABLE_PYFILE 2&>/dev/null
rm /tmp/*pymode* 2&>/dev/null
rm -rf /tmp/pack
mkdir -p /tmp/pack/test_plugins/start
ln -s $(dirname $(pwd)) /tmp/pack/test_plugins/start/
set -e

# vim: set fileformat=unix filetype=sh wrap tw=0 :
