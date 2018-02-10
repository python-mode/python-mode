" Test that the PymodeLintAuto changes a badly formated buffer.

" For safety empty current buffer.
execute "normal! :%d\<CR>"

" Load sample python file.
read ./test_python_sample_code/folding2.py

" Delete the first line (which is not present in the original file) and save
" loaded file.
execute "normal! gg"
execute "normal! dd"
noautocmd write!

set fdm=marker
set fdm=expr

let foldlevels = ['a1', '=', '=', '=', '=', '=', 's1', '=', '=', '=', '=',
                  \ '0', '>1', '=', '>2', '=', '=', '=', '=', '=', '1', '=',
                  \ '0', '>1', 'a1', '=', 's1', '=', '=', '>2', '=', '>3', '=',
                  \ 'a1', '=', '=', '=', 's1', '=', '=', '=', '=', '=', '=',
                  \'=', '=', '=', '=', '2', '=', '=', '1', '=', '0', '0', '0']

if len(foldlevels) != line('$')
    echoerr 'Unmatching loaded file and foldlevels list.'
endif

let i = 1
for fdl in foldlevels
    let calc = pymode#debug#foldingexpr(i)
    let stored = fdl
    call assert_true(calc == stored)
    let i += 1
endfor

" Assert changes.
if len(v:errors) > 0
    cquit!
else
    quit!
endif
