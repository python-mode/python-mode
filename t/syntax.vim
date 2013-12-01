describe 'pymode-syntax'

    before
        syntax on
        set filetype=python
    end

    after
        bd!
    end

    it 'pymode-syntax options'
        Expect g:pymode_syntax == 1
        Expect g:pymode_syntax_all == 1
        Expect g:pymode_syntax_print_as_function == 0
        Expect g:pymode_syntax_highlight_equal_operator == 1
        Expect g:pymode_syntax_highlight_stars_operator == 1
        Expect g:pymode_syntax_highlight_self == 1
        Expect g:pymode_syntax_indent_errors == 1
        Expect g:pymode_syntax_space_errors == 1
        Expect g:pymode_syntax_string_formatting == 1
        Expect g:pymode_syntax_string_format == 1
        Expect g:pymode_syntax_string_templates == 1
        Expect g:pymode_syntax_doctests == 1
        Expect g:pymode_syntax_builtin_objs == 1
        Expect g:pymode_syntax_builtin_types == 1
        Expect g:pymode_syntax_builtin_funcs == 1
        Expect g:pymode_syntax_highlight_exceptions == 1
        Expect g:pymode_syntax_slow_sync == 1
    end

end

