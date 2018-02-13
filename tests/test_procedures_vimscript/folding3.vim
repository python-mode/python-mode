" Test that doing (reversible) changes in insert mode or normal mode to a
" buffer do not alter their folding.

" Load sample python file.
read ./test_python_sample_code/algorithms.py

" Delete the first line (which is not present in the original file) and save
" loaded file.
execute "normal! gg"
execute "normal! dd"
noautocmd write!

" Load auxiliary code.
source ./test_helpers_vimscript/inserting_text.vim
source ./test_helpers_vimscript/md5sum.vim

" Get original md5sum for script.
noautocmd write!
call Md5()
let s:md5orig = b:calculated_md5
unlet b:calculated_md5

" Define a convenient function to map line numbers to their folding values.
function Pymodefoldingfuncref(key, val)
    let l:retval = pymode#folding#expr(a:val)
    return l:retval
endfunction!


" Force recomputation of all foldings.
" TODO: inspect why causes trouble.
" set fdm=expr
" set fdm=marker
" set fdm=expr
let b:old_fold_vals = map(range(1, line('$')), function('Pymodefoldingfuncref'))

" Change folding in numerous ways.
call InsertTextAtRandomPositions(10)

" Force recomputation of all foldings.
" set fdm=expr
" set fdm=marker
" set fdm=expr
let b:new_fold_vals = map(range(1, line('$')), function('Pymodefoldingfuncref'))

" Get original md5sum for script.
noautocmd write!
call Md5()
let s:md5mod = b:calculated_md5
unlet b:calculated_md5

" echom s:md5orig == s:md5mod
" echom b:new_fold_vals ==  b:old_fold_vals

" set fdm=expr
" set fdm=marker
" set fdm=expr

" Assert changes.
call assert_equal(s:md5orig, s:md5mod)
call assert_equal(b:new_fold_vals, b:old_fold_vals)
if len(v:errors) > 0
    cquit!
else
    quit!
endif
