" Test that the PymodeLintAuto changes a badly formated buffer.

" Load sample python file.
read ./test_python_sample_code/from_autopep8.py

" Delete the first line (which is not present in the original file) and save
" loaded file.
execute "normal! gg"
execute "normal! dd"
noautocmd write!

" HOW TO BREAK: Remove very wrong python code leading to a short loclist of
" errors.
" Introduce errors.
" execute "normal! :%d\<CR>"

" Start with an empty loclist.
call assert_true(len(getloclist(0)) == 0)
PymodeLint
call assert_true(len(getloclist(0)) > 5)
write!

" Assert changes.
if len(v:errors) > 0
    cquit!
else
    quitall!
endif
