" Test that the PymodeLintAuto changes a badly formated buffer.

" Load sample python file.
read ./test_python_sample_code/from_autopep8.py

" Load auxiliary code.
source ./test_helpers_vimscript/md5sum.vim

" Delete the first line (which is not present in the original file) and save
" loaded file.
execute "normal! gg"
execute "normal! dd"
noautocmd write!

" Get original md5sum for script.
call Md5()
let s:md5orig = b:calculated_md5
unlet b:calculated_md5

" Change the buffer.
PymodeLintAuto
write!

" Get different md5sum for script.
call Md5()
let s:md5mod = b:calculated_md5

" Assert changes.
call assert_notequal(s:md5orig, s:md5mod)
if len(v:errors) > 0
    cquit!
else
    quit!
endif
