filetype plugin indent on
set hidden

describe 'pymode'

    it 'pymode disabled by default'
        Expect get(g:, 'pymode', 42) == 42
    end

    it 'pymode loading'
        e t/test.py
        Expect g:pymode == 1
        Expect g:pymode_init == 1
        Expect g:pymode_path == 1
        Expect g:pymode_lint == 1
    end

    it 'pymode python interpreter'
        e test.py
        Python vim.current.buffer.append('Python is working.', 0)
        Expect getline(1) == 'Python is working.'
    end

end
