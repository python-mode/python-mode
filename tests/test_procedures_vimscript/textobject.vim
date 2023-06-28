set noautoindent
let g:pymode_rope=1

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


" Clean file.
%delete

" With 'def'.
execute "normal! iprint(\<CR>    1\<CR>)\<CR>"
execute "normal! iprint(\<CR>    2\<CR>)\<CR>"
execute "normal! iprint(\<CR>    3\<CR>)\<CR>"
normal 4ggdV

let content=getline('^', '$')
call assert_true(content == [
\    "print(", "    1", ")",
\    "print(", "    3", ")",
\    ""
\])


" Clean file.
%delete

" With 'def'.
execute "normal! iprint(\<CR>    1\<CR>)\<CR>"
execute "normal! iprint(\<CR>    2\<CR>)\<CR>"
execute "normal! iprint(\<CR>    3\<CR>)\<CR>"
execute "normal! iprint(\<CR>    4\<CR>)\<CR>"
normal 5ggd2V

let content=getline('^', '$')
call assert_true(content == [
\    "print(", "    1", ")",
\    "print(", "    4", ")",
\    ""
\])

" Clean file.
%delete

" With 'def'.
execute "normal! iprint(\<CR>    1\<CR>)\<CR>"
execute "normal! iprint(\<CR>    2\<CR>)\<CR>"
execute "normal! iprint(\<CR>    3\<CR>)\<CR>"
execute "normal! iprint(\<CR>    4\<CR>)\<CR>"
normal 5ggd2V

let content=getline('^', '$')
call assert_true(content == [
\    "print(", "    1", ")",
\    "print(", "    4", ")",
\    ""
\])

if len(v:errors) > 0
    cquit!
else
    quit!
endif
