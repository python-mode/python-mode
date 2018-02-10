#! /bin/bash

# TODO XXX: improve python-mode testing asap.
# Test all python commands.

# Execute tests.
declare -a TEST_PYMODE_COMMANDS_ARRAY=(
    "./test_procedures_vimscript/pymodeversion.vim"
    "./test_procedures_vimscript/pymodelint.vim"
    "./test_procedures_vimscript/pymoderun.vim"
    )

### Enable the following to execute one test at a time.
### FOR PINPOINT TESTING ### declare -a TEST_PYMODE_COMMANDS_ARRAY=(
### FOR PINPOINT TESTING ###     "./test_procedures_vimscript/pymoderun.vim"
### FOR PINPOINT TESTING ###     )

## now loop through the above array
set +e
for ONE_PYMODE_COMMANDS_TEST in "${TEST_PYMODE_COMMANDS_ARRAY[@]}"
do
    echo "Starting test: $0:$ONE_PYMODE_COMMANDS_TEST" >> $VIM_OUTPUT_FILE
    RETURN_CODE=$(vim -i NONE -u $VIM_TEST_VIMRC -c "source $ONE_PYMODE_COMMANDS_TEST" $VIM_DISPOSABLE_PYFILE > /dev/null 2>&1)

    ### Enable the following to execute one test at a time.
    ### FOR PINPOINT TESTING ### vim -i NONE -u $VIM_TEST_VIMRC -c "source $ONE_PYMODE_COMMANDS_TEST" $VIM_DISPOSABLE_PYFILE
    ### FOR PINPOINT TESTING ### exit 1

    RETURN_CODE=$?
    echo -e "\n$0:$ONE_PYMODE_COMMANDS_TEST: Return code: $RETURN_CODE" >> $VIM_OUTPUT_FILE
    bash ./test_helpers_bash/test_prepare_between_tests.sh
done

# vim: set fileformat=unix filetype=sh wrap tw=0 :
