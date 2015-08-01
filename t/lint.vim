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

    it 'lint new'
        put =['# coding: utf-8', 'x = 1']
        PymodeLint
        Expect getloclist(0) ==  []
    end

    it 'lint code'
        e t/test.py
        PymodeLint
        let ll = getloclist(0)

        Expect len(ll) == 2

        Expect ll[0]['lnum'] == 6
        Expect ll[0]['col'] == 7
        Expect ll[0]['type'] == 'C'
        Expect ll[0]['valid'] == 1
        Expect ll[0]['text'] == 'E225 missing whitespace around operator [pep8]'

        Expect ll[1]['lnum'] == 9
        Expect ll[1]['col'] == 1
        Expect ll[1]['type'] == 'E'
        Expect ll[1]['valid'] == 1
        Expect ll[1]['text'] == "E0602 undefined name 'unknown' [pyflakes]"
    end

end
