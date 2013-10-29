filetype plugin indent on
set hidden

describe 'pymode check code'

    before
        e t/test.py
    end

    after
        close
    end

    it 'async'
        let g:pymode_lint_async = 1
        PyLint
        Expect getqflist() == []
        sleep 1
        call pymode#queue#Poll()
        Expect getqflist() == [{'lnum': 2, 'bufnr': 1, 'col': 0, 'valid': 1, 'vcol': 0, 'nr': 0, 'type': 'E', 'pattern': '', 'text': 'W0612 local variable "test" is assigned to but never used [pyflakes]'}]
    end

    it 'disable async'
        let g:pymode_lint_async = 0
        PyLint
        Expect getqflist() == [{'lnum': 2, 'bufnr': 1, 'col': 0, 'valid': 1, 'vcol': 0, 'nr': 0, 'type': 'E', 'pattern': '', 'text': 'W0612 local variable "test" is assigned to but never used [pyflakes]'}]
    end

end

