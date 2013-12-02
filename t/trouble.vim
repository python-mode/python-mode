source  plugin/pymode.vim 

describe 'pymode troubleshooting'

    after
        bd!
        bd!
    end

    it 'pymode troubleshooting'
        call pymode#troubleshooting#test()
        Expect getline(1) == 'Pymode diagnostic'
    end

end
