let g:pymode_rope_completion_bind = 'X'
let g:pymode_rope_autoimport = 0
let g:pymode_debug = 1

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
        let project_path = '.ropeproject'
        Expect isdirectory(project_path)  == 0
        normal oimporX
        Expect getline('.') == 'import'
        Expect isdirectory(project_path)  == 1
    end

end
