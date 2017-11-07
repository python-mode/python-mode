describe 'pymode-virtualenv'

    before
        source  plugin/pymode.vim 
        set filetype=python
    end

    after
        bd!
    end

    " TODO: How can we mock the virtualenv activation to check that the
    " proper path is set to pymode_virtualenv_enabled? Right now, the 
    " python function enable_virtualenv gets called but fails when trying
    " to actually activate so the env.let never gets called

    it 'accepts relative paths'
        call pymode#virtualenv#activate("sample/relative/path")
        " Our path variable is the path argument
        Expect g:pymode_virtualenv_path == "sample/relative/path"
    end

    it 'accepts absolute paths'
        call pymode#virtualenv#activate("/sample/absolute/path")
        " Our path variable is the path argument
        Expect g:pymode_virtualenv_path == "/sample/absolute/path"
    end
end
