" DESC: Set scriptname
let g:scriptname = expand("<sfile>:t")

" OPTION: g:pymode_utils -- bool. Load utils
call helpers#SafeVar("g:pymode_utils", 1)

" OPTION: g:pymode_utils_whitespaces -- bool. Remove unused whitespaces on save
call helpers#SafeVar("g:pymode_utils_whitespaces", 1)

" DESC: Disable script loading
if helpers#SafeVar("b:utils", 1) || g:pymode_utils == 0
    finish
endif

" DESC: Set autocommands
if g:pymode_utils_whitespaces
    au BufWritePre <buffer> :call setline(1,map(getline(1,"$"),'substitute(v:val,"\\s\\+$","","")'))
endif
