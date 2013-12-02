describe 'pymode-plugin'

    before
        source  plugin/pymode.vim 
        set filetype=python
    end

    after
        bd!
    end

    it 'pymode options'
        Expect g:pymode == 1
        Expect g:pymode_python == 'python'
        Expect g:pymode_paths == []
        Expect g:pymode_virtualenv == 1
        Expect g:pymode_run == 1
        Expect g:pymode_lint == 1
        Expect g:pymode_breakpoint == 1
        Expect g:pymode_doc == 1
        Expect g:pymode_indent == 1
    end

    it 'pymode interpreter'
        PymodePython import vim
        PymodePython vim.current.buffer.append('test success')
        Expect getline('$') == 'test success'
    end

    it 'pymode save'
        Expect expand('%') == ''
        Expect pymode#save() == 0
    end

end


describe 'pymode-python-disable'
    before
        let g:pymode_python = 'disable'
        source  plugin/pymode.vim 
        set filetype=python
    end

    after
        bd!
    end

    it 'pymode disable python'
        Expect g:pymode_doc        == 0
        Expect g:pymode_lint       == 0
        Expect g:pymode_path       == 0
        Expect g:pymode_rope       == 0
        Expect g:pymode_run        == 0
        Expect g:pymode_virtualenv == 0
    end

end
