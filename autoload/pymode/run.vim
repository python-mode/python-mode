" DESC: Save file if it modified and run python code
fun! pymode#run#Run() "{{{
    if &modifiable && &modified | write | endif	
    call pymode#ShowCommand(g:python . " " . expand("%:p"))
endfunction "}}}
