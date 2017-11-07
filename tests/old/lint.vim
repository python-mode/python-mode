source  plugin/pymode.vim 

describe 'pymode check code'

    before
        set ft=python
    end

    after
        bd!
    end

    it 'pymode lint loaded'
        Expect g:pymode_lint == 1
    end

    it 'lint new'
        put =['# coding: utf-8', 'call_unknown_function()']
        PymodeLint
        Expect getloclist(0) ==  []
    end

    it 'lint code'
        e t/test.py
        PymodeLint
        Expect getloclist(0) ==  [{'lnum': 6, 'bufnr': 1, 'col': 0, 'valid': 1, 'vcol': 0, 'nr': 0, 'type': 'E', 'pattern': '', 'text': 'W0612 local variable "unused" is assigned to but never used [pyflakes]'}, {'lnum': 8, 'bufnr': 1, 'col': 0, 'valid': 1, 'vcol': 0, 'nr': 0, 'type': 'E', 'pattern': '', 'text': 'E0602 undefined name "unknown" [pyflakes]'}]
    end

end

