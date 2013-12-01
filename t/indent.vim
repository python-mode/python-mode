source  plugin/pymode.vim 

describe 'indent'

    before
        set ft=python
        source after/indent/python.vim
    end

    after
        bd!
    end

    it 'pymode indent loaded'
        Expect g:pymode_indent == 1
        Expect &expandtab == 1
        Expect &shiftround == 1
        Expect &autoindent == 1
        Expect &indentexpr == 'pymode#indent#get_indent(v:lnum)'
    end

end

