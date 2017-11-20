" Test that the PymodeLintAuto changes a badly formated buffer.

" Load sample python file.
read ./test_python_sample_code/pymoderun_sample.py

" Delete the first line (which is not present in the original file) and save
" loaded file.
execute "normal! gg"
execute "normal! dd"
noautocmd write!

" Allow switching to windows with buffer command.
let s:curr_buffer = bufname("%")
set switchbuf+=useopen

" Change the buffer.
PymodeRun
write!
let run_buffer = bufname("run")
execute "buffer " . run_buffer

" Assert changes.

" There exists a buffer.
call assert_true(len(run_buffer) > 0)

" This buffer has more than five lines.
call assert_true(line('$') > 5)

if len(v:errors) > 0
    cquit!
else
    quit!
endif
