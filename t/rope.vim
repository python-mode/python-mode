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
        let project_path = getcwd() . system("mktemp -u /.ropeproject.XXXXXX | tr -d '\n'")
        Expect isdirectory(project_path)  == 0
        let g:pymode_rope_project_root = project_path
        normal oimporX
        Expect getline('.') == 'import'
        Expect g:pymode_rope_current == project_path . '/'
        Expect isdirectory(project_path)  == 1
    end

end
