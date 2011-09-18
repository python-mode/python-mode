if helpers#SafeVar("b:utils", 1)
    finish
endif

" Trim trailing whitespace
call helpers#SafeVar("g:pymode_whitespaces", 1)
if g:pymode_whitespaces
    au BufWritePre <buffer> :call setline(1,map(getline(1,"$"),'substitute(v:val,"\\s\\+$","","")'))
endif
