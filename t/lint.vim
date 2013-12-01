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

end

