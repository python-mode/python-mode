let g:PymodeSigns = {}


fun! pymode#tools#signs#init() "{{{
    call g:PymodeSigns.setup()
endfunction "}}}


fun! g:PymodeSigns.enabled() "{{{
    return (g:pymode_lint_signs && has('signs'))
endfunction "}}}


fun! g:PymodeSigns.setup() "{{{
    if self.enabled()
        execute 'sign define PymodeW text=' . g:pymode_lint_todo_symbol     . " texthl=Todo"
        execute 'sign define PymodeD text=' . g:pymode_lint_docs_symbol     . " texthl=String"
        execute 'sign define PymodeC text=' . g:pymode_lint_comment_symbol  . " texthl=Comment"
        execute 'sign define PymodeR text=' . g:pymode_lint_visual_symbol   . " texthl=Visual"
        execute 'sign define PymodeE text=' . g:pymode_lint_error_symbol    . " texthl=Error"
        execute 'sign define PymodeI text=' . g:pymode_lint_info_symbol     . " texthl=Info"
        execute 'sign define PymodeF text=' . g:pymode_lint_pyflakes_symbol . " texthl=Info"
    endif
    let self._sign_ids = []
    let self._next_id = 10000
    let self._messages = {}
endfunction "}}}


fun! g:PymodeSigns.refresh(loclist) "{{{
    if self.enabled()
        call self.clear()
        call self.place(a:loclist)
    endif
endfunction "}}}


fun! g:PymodeSigns.clear() "{{{
    let ids = copy(self._sign_ids)
    for i in ids
        execute "sign unplace " . i
        call remove(self._sign_ids, index(self._sign_ids, i))
    endfor
endfunction "}}}


fun! g:PymodeSigns.place(loclist) "{{{
    let seen = {}
    for issue in a:loclist.loclist()
        if !has_key(seen, issue.lnum)
            let seen[issue.lnum] = 1
            call add(self._sign_ids, self._next_id)
            execute printf('sign place %d line=%d name=%s buffer=%d', self._next_id, issue.lnum, "Pymode".issue.type[0], issue.bufnr)
            let self._next_id += 1
        endif
    endfor
endfunction "}}}
