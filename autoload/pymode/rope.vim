" Python-mode Rope support
"
PymodePython from pymode import rope


fun! pymode#rope#completions(findstart, base)
    PymodePython rope.completions()
endfunction

fun! pymode#rope#complete(dot)
    if pumvisible()
        return "\<C-n>"
    end
    if a:dot
        PymodePython rope.complete(True)
    else
        PymodePython rope.complete()
    end
    return pumvisible() ? "\<C-p>\<Down>" : ""
endfunction

fun! pymode#rope#complete_on_dot() "{{{
    if !exists("*synstack")
        return ""
    end
    for group in map(synstack(line('.'), col('.') - 1), 'synIDattr(v:val, "name")')
        for name in ['pythonString', 'pythonComment', 'pythonNumber']
            if group == name
                return "" 
            endif
        endfor
    endfor
    return pymode#rope#complete(1)
endfunction "}}}

fun! pymode#rope#goto_definition()
    PymodePython rope.goto()
endfunction


fun! pymode#rope#organize_imports()
    if !pymode#save()
        return 0
    endif
    call pymode#wide_message('Organize imports ... ')
    PymodePython rope.organize_imports()
endfunction


fun! pymode#rope#find_it()
    let l:output = []
    call pymode#wide_message('Finding Occurrences ...')
    PymodePython rope.find_it()
    call pymode#wide_message('')
    if !empty(l:output)
        call setqflist(l:output)
        call pymode#quickfix_open(0, g:pymode_lint_hold, g:pymode_lint_maxheight, g:pymode_lint_minheight, 0)
    end
endfunction


fun! pymode#rope#show_doc()
    let l:output = []

    PymodePython rope.show_doc()

    if !empty(l:output)
        call pymode#tempbuffer_open('__doc____rope__')
        call append(0, l:output)
        wincmd p
    end
endfunction


fun! pymode#rope#regenerate() "{{{
    PymodePython rope.regenerate()
endfunction "}}}


fun! pymode#rope#new() "{{{
    PymodePython rope.new()
endfunction "}}}


fun! pymode#rope#rename() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.RenameRefactoring().run()
endfunction "}}}

fun! pymode#rope#rename_module() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.RenameRefactoring(True).run()
endfunction "}}}

fun! pymode#rope#extract_method() range "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.ExtractMethodRefactoring().run()
endfunction "}}}

fun! pymode#rope#extract_variable() range "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.ExtractVariableRefactoring().run()
endfunction "}}}

fun! pymode#rope#undo() "{{{
    PymodePython rope.undo()
endfunction "}}}

fun! pymode#rope#redo() "{{{
    PymodePython rope.redo()
endfunction "}}}

fun! pymode#rope#inline() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.InlineRefactoring().run()
endfunction "}}}

fun! pymode#rope#move() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.MoveRefactoring().run()
endfunction "}}}

fun! pymode#rope#use_function() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.UseFunctionRefactoring().run()
endfunction "}}}

fun! pymode#rope#module_to_package() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.ModuleToPackageRefactoring().run()
endfunction "}}}
