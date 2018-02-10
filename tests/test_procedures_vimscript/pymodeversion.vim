" Test that the PymodeLintAuto changes a badly formated buffer.

" Clear messages.
messages clear

" Produce expected message.
PymodeVersion
let s:msg = execute('messages')

" Assert changes.
call assert_match('pymode version', tolower(s:msg))

if len(v:errors) > 0
    cquit!
else
    quit!
endif
