function! InsertRandomText(low_range, high_range) " {{{
    " Insert random ascii visible table text at cursor position.
    " Return the number of characters inserted.

python3 << EOF
import random, string, vim
# Text has to large from a larger sample in order to avoid errors.
text = random.sample(
    (10 * string.ascii_lowercase + string.digits + ' '),
    random.randint(int(vim.eval('a:low_range')), int(vim.eval('a:high_range'))))
vim.current.buffer.vars['random_text'] = ''.join(text)
EOF
let l:textwidth = &tw
set tw=0
execute "normal! i" . b:random_text
let &tw = l:textwidth

return len(b:random_text)

endfunction " }}}

function! DeleteChars(nchars) " {{{
    " Delete n chars at cursor position.
    " It is the inverse of InsertRandomText().

    let l:textwidth = &tw
    set tw=0
    execute "normal! " . (repeat('h', a:nchars - 1))
    execute "normal! " . repeat('x', a:nchars)
    let &tw = l:textwidth

endfunction " }}}

function! JumpToRandomPosition() " {{{
" Jump cursor to a random position in current buffer.

python3 << EOF
import random, vim
cw = vim.current.window
cb = vim.current.buffer
rand_line = random.randint(1, len(cb) - 1)
rand_line_len = len(cb[rand_line])
rand_col = random.randint(0, rand_line_len) if rand_line_len > 0 else 0
cw.cursor = (rand_line, rand_col)
EOF
endfunction " }}}

function! DeleteRandomLines(low_range, high_range) " {{{
" Delete random lines between low_range and high_range.
" Return the number of lines deleted.

python3 << EOF
import random, vim
del_lines = random.randint(
    int(vim.eval('a:low_range')), int(vim.eval('a:high_range')))
vim.current.buffer.vars['del_lines'] = del_lines
EOF

execute "normal! " . b:del_lines . "dd"

return b:del_lines

endfunction "}}}

function! InsertTextAtRandomPositions(ntimes) " {{{
" Insert text at random positions. May either insert in insert mode or in
" normal mode.

    let l:total_lines = line('$')
    for i in range(a:ntimes)

python3 << EOF
import random, vim
del_method = random.randint(0, 1)
vim.current.buffer.vars['del_method'] = del_method
EOF

        call JumpToRandomPosition()
        " b:del_method is set to either change the buffer via insert mode or
        " via normal mode.
        if b:del_method
            " This uses insert mode.
            let l:inserted_chars = InsertRandomText(3, 100)
            call DeleteChars(l:inserted_chars)
        else
            " This uses normal mode.
            let l:current_line  = getpos('.')[1]
            let l:deleted_lines = DeleteRandomLines(1, 5)
            if l:current_line + l:deleted_lines <= l:total_lines
                execute "normal! P"
            else
                execute "normal! p"
            endif
        endif

    endfor

endfunction " }}}
