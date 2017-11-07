source  plugin/pymode.vim 

describe 'pymode-ftplugin'

    before
        set filetype=python
    end

    after
        bd!
    end

    it 'pymode init'
        PymodePython import pymode
    end

end

