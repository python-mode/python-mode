" Common setup for all Vader tests
" This file is included by all test files to ensure consistent environment

" Ensure python-mode is loaded
if !exists('g:pymode')
    runtime plugin/pymode.vim
endif

" Basic python-mode configuration for testing
let g:pymode = 1
let g:pymode_python = 'python3'
let g:pymode_options_max_line_length = 79
let g:pymode_lint_on_write = 0
let g:pymode_rope = 0
let g:pymode_doc = 1
let g:pymode_virtualenv = 0
let g:pymode_folding = 1
let g:pymode_motion = 1
let g:pymode_run = 1

" Test-specific settings
let g:pymode_lint_checkers = ['pyflakes', 'pep8', 'mccabe']
let g:pymode_lint_ignore = []
let g:pymode_options_colorcolumn = 1

" Disable features that might cause issues in tests
let g:pymode_breakpoint = 0
let g:pymode_debug = 0

" Helper functions for tests
function! SetupPythonBuffer()
    " Create a new buffer with Python filetype
    new
    setlocal filetype=python
    setlocal buftype=
    " Explicitly load the python ftplugin to ensure commands are available
    runtime! ftplugin/python/pymode.vim
endfunction

function! CleanupPythonBuffer()
    " Clean up test buffer
    if &filetype == 'python'
        bwipeout!
    endif
endfunction

function! GetBufferContent()
    " Get all lines from current buffer
    return getline(1, '$')
endfunction

function! SetBufferContent(lines)
    " Set buffer content from list of lines
    call setline(1, a:lines)
endfunction

function! AssertBufferContains(pattern)
    " Assert that buffer contains pattern
    let content = join(getline(1, '$'), "\n")
    if content !~# a:pattern
        throw 'Buffer does not contain pattern: ' . a:pattern
    endif
endfunction

function! AssertBufferEquals(expected)
    " Assert that buffer content equals expected lines
    let actual = getline(1, '$')
    if actual != a:expected
        throw 'Buffer content mismatch. Expected: ' . string(a:expected) . ', Got: ' . string(actual)
    endif
endfunction

" Python code snippets for testing
let g:test_python_simple = [
    \ 'def hello():',
    \ '    print("Hello, World!")',
    \ '    return True'
    \ ]

let g:test_python_unformatted = [
    \ 'def test():    return 1',
    \ 'class   TestClass:',
    \ '  def method(self):',
    \ '      pass'
    \ ]

let g:test_python_formatted = [
    \ 'def test():',
    \ '    return 1',
    \ '',
    \ '',
    \ 'class TestClass:',
    \ '    def method(self):',
    \ '        pass'
    \ ]

let g:test_python_with_errors = [
    \ 'def test():',
    \ '    undefined_variable',
    \ '    return x + y'
    \ ]

let g:test_python_long_line = [
    \ 'def very_long_function_name_that_exceeds_line_length_limit(parameter_one, parameter_two, parameter_three, parameter_four):',
    \ '    return parameter_one + parameter_two + parameter_three + parameter_four'
    \ ]