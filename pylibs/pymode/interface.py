import vim


def get_option(name):
    return vim.eval("pymode#Option('%s')" % name)


def get_var(name):
    return vim.eval("g:pymode_%s" % name)


def get_current_buffer():
    return vim.current.buffer


def show_message(message):
    vim.command("call pymode#WideMessage('%s')" % message)


def command(cmd):
    vim.command(cmd)
