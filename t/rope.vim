let g:pymode_rope_completion_bind = 'X'
let g:pymode_rope_autoimport = 0
let g:pymode_debug = 1
let g:pymode_rope_lookup_project = 0

source  plugin/pymode.vim 

describe 'pymode-plugin'

    before
        set filetype=python
    end

    after
        bd!
        bd!
    end

    it 'pymode rope auto open project in current working directory'

        if $TRAVIS != ""
            SKIP 'Travis fails on this test'
        endif

        let project_path = getcwd() . '/.ropeproject'
        Expect isdirectory(project_path)  == 0
        normal oimporX
        Expect getline('.') == 'import'
        Expect g:pymode_rope_current == getcwd() . '/'
        Expect g:pymode_rope_current . '.ropeproject' == project_path
        Expect isdirectory(project_path)  == 1
    end

end
