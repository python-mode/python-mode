" Python-mode Rope support

if ! g:pymode_rope
    finish
endif

PymodePython from pymode import rope

call pymode#tools#loclist#init()


fun! pymode#rope#completions(findstart, base)
    PymodePython rope.completions()
endfunction

fun! pymode#rope#complete(dot)
    if pumvisible()
        if stridx('noselect', &completeopt) != -1
            return "\<C-n>"
        else
            return ""
        endif
    endif
    if a:dot
        PymodePython rope.complete(True)
    else
        PymodePython rope.complete()
    endif
    return pumvisible() && stridx('noselect', &completeopt) != -1 ? "\<C-p>\<Down>" : ""
endfunction

fun! pymode#rope#complete_on_dot() "{{{
    if !exists("*synstack")
        return ""
    endif
    for group in map(synstack(line('.'), col('.') - 1), 'synIDattr(v:val, "name")')
        for name in ['pythonString', 'pythonComment', 'pythonNumber', 'pythonDocstring']
            if group == name
                return ""
            endif
        endfor
    endfor
    if g:pymode_rope_autoimport_import_after_complete
        PymodePython rope.complete_check()
    endif
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
    let loclist = g:PymodeLocList.current()
    let loclist._title = "Occurrences"
    call pymode#wide_message('Finding Occurrences ...')
    PymodePython rope.find_it()
    call loclist.show()
endfunction


fun! pymode#rope#show_doc()
    let l:output = []

    PymodePython rope.show_doc()

    if !empty(l:output)
        call pymode#tempbuffer_open('__doc____rope__')
        call append(0, l:output)
        setlocal nomodifiable
        setlocal nomodified
        setlocal filetype=rst

        normal gg

        wincmd p
    endif
endfunction


fun! pymode#rope#regenerate() "{{{
    call pymode#wide_message('Regenerate Rope cache ... ')
    PymodePython rope.regenerate()
endfunction "}}}


fun! pymode#rope#new(...) "{{{
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

fun! pymode#rope#signature() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.ChangeSignatureRefactoring().run()
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

fun! pymode#rope#autoimport(word) "{{{
    PymodePython rope.autoimport()
endfunction "}}}

fun! pymode#rope#generate_function() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.GenerateElementRefactoring('function').run()
endfunction "}}}

fun! pymode#rope#generate_class() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.GenerateElementRefactoring('class').run()
endfunction "}}}

fun! pymode#rope#generate_package() "{{{
    if !pymode#save()
        return 0
    endif
    PymodePython rope.GenerateElementRefactoring('package').run()
endfunction "}}}
