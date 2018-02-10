" Test that doing (reversible) changes in insert mode or normal mode to a
" buffer do not alter their folding.

" Load sample python file.
" With 'def'.
execute "normal! idef myfunc():\<CR>    a=1"
execute "normal! A; a= 2;"

" Clean file.
execute "normal! :%d\<CR>"

" With 'class'.
execute "normal! iclass MyClass():\<CR>    a=1"
execute "normal! A; a= 2;"

quit!
