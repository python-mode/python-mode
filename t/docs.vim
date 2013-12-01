source  plugin/pymode.vim 

describe 'docs'
    before
        set filetype=python
    end

    after
        bd!
        bd!
    end

    it 'pymode show docs'
        Expect g:pymode_doc == 1
        put = 'def'
        normal GK
        wincmd p
        Expect bufname('%') == "__doc__"
        Expect getline(1) == 'Function definitions'
        Expect &filetype == 'rst'
    end

end

