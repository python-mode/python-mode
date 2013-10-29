filetype plugin indent on
set hidden

describe 'docs'
    before
        e t/test.py
        let g:pymode_test = 1
    end

    it 'pymode indent loaded'
        Expect &indentexpr == 'pymode#indent#Indent(v:lnum)'
    end

    after
        close
    end

end

