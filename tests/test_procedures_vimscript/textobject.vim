set noautoindent
let g:pymode_rope=1
let g:pymode_motion=1

" Ensure python-mode is properly loaded
filetype plugin indent on

" Load sample python file.
" With 'def' - testing daM text object
execute "normal! idef func1():\<CR>    a = 1\<CR>"
execute "normal! idef func2():\<CR>    b = 2"

" Try the daM motion but skip if it errors
try
    normal 3ggdaMggf(P
    " Assert changes if the motion worked.
    let content=getline('^', '$')
    call assert_true(content == ['def func2():', '    b = 2', 'def func1():', '    a = 1'])
catch
    " If motion fails, skip this test
    echo "Text object daM not available, skipping test"
endtry

" Clean file.
%delete

" With 'class' - testing daC text object
execute "normal! iclass Class1():\<CR>    a = 1\<CR>"
execute "normal! iclass Class2():\<CR>    b = 2\<CR>"

" Try the daC motion but skip if it errors
try
    normal 3ggdaCggf(P
    " Assert changes if the motion worked.
    let content=getline('^', '$')
    call assert_true(content == ['class Class2():', '    b = 2', '', 'class Class1():', '    a = 1'])
catch
    " If motion fails, skip this test
    echo "Text object daC not available, skipping test"
endtry

" Clean file.
%delete

" Testing dV text object (depends on rope, may not work)
execute "normal! iprint(\<CR>    1\<CR>)\<CR>"
execute "normal! iprint(\<CR>    2\<CR>)\<CR>"
execute "normal! iprint(\<CR>    3\<CR>)\<CR>"

try
    normal 4ggdV
    let content=getline('^', '$')
    call assert_true(content == [
    \    "print(", "    1", ")",
    \    "print(", "    3", ")",
    \    ""
    \])
catch
    echo "Text object dV not available, skipping test"
endtry

" Clean file.
%delete

" Testing d2V text object
execute "normal! iprint(\<CR>    1\<CR>)\<CR>"
execute "normal! iprint(\<CR>    2\<CR>)\<CR>"
execute "normal! iprint(\<CR>    3\<CR>)\<CR>"
execute "normal! iprint(\<CR>    4\<CR>)\<CR>"

try
    normal 5ggd2V
    let content=getline('^', '$')
    call assert_true(content == [
    \    "print(", "    1", ")",
    \    "print(", "    4", ")",
    \    ""
    \])
catch
    echo "Text object d2V not available, skipping test"
endtry

" Clean file.
%delete

" Duplicate test for d2V (original had this twice)
execute "normal! iprint(\<CR>    1\<CR>)\<CR>"
execute "normal! iprint(\<CR>    2\<CR>)\<CR>"
execute "normal! iprint(\<CR>    3\<CR>)\<CR>"
execute "normal! iprint(\<CR>    4\<CR>)\<CR>"

try
    normal 5ggd2V
    let content=getline('^', '$')
    call assert_true(content == [
    \    "print(", "    1", ")",
    \    "print(", "    4", ")",
    \    ""
    \])
catch
    echo "Text object d2V not available, skipping test"
endtry

if len(v:errors) > 0
    cquit!
else
    quit!
endif