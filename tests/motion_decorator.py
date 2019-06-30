#!coding=utf-8
"""
to test pymode motions, please put cursor on each of the lines
and press "vaM" for selecting methods or
"vaC" for selection class.
"""

def a_decorator(func):
    print("chamando func")
    def wrapped(*args, **kw):
        return func(*args, **kw)
    print("Pós func")
    return wrapped

def b_decorator(func):
    print("second chamando func")
    def wrapped(*args, **kw):
        return func(*args, **kw)
    print("second Pós func")
    return wrapped

@b_decorator
@a_decorator
def teste():
    print("Not Selecting Decorator")

class Teste:
    @a_decorator
    @b_decorator
    def metodo(self):
        print("Meu método")


teste()

testinho = Teste()
testinho.metodo()
