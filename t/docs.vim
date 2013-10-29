filetype plugin indent on
set hidden

describe 'docs'
    before
        e t/test.py
        let g:pymode_test = 1
    end

    it 'pymode show docs'
        Pydoc def
        Expect getline(1) == 'Function definitions'
    end

end

