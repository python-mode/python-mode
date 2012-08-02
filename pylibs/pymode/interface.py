import vim


def get_option(name):
    return get_bvar(name) or get_var(name)


def get_var(name):
    return vim.eval("g:pymode_%s" % name)


def get_bvar(name):
    return (int(vim.eval("exists('b:pymode_%s')" % name)) and vim.eval("b:pymode_%s" % name)) or None


def get_current_buffer():
    return vim.current.buffer


def show_message(message):
    vim.command("call pymode#WideMessage('%s')" % message)


def command(cmd):
    vim.command(cmd)
