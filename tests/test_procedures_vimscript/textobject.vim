" Load sample python file.
" With 'def'.
execute "normal! idef func1():\<CR>    a = 1\<CR>"
execute "normal! idef func2():\<CR>    b = 2"
normal 3ggdaMggf(P

" Assert changes.
let content=getline('^', '$')
call assert_true(content == ['def func2():', '    b = 2', 'def func1():', '    a = 1'])


" Clean file.
%delete

" With 'class'.
execute "normal! iclass Class1():\<CR>    a = 1\<CR>"
execute "normal! iclass Class2():\<CR>    b = 2\<CR>"
normal 3ggdaCggf(P

" Assert changes.
let content=getline('^', '$')
call assert_true(content == ['class Class2():', '    b = 2', '', 'class Class1():', '    a = 1'])


if len(v:errors) > 0
    cquit!
else
    quit!
endif
