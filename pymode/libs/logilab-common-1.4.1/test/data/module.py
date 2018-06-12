# -*- coding: Latin-1 -*-
"""test module for astng
"""
from __future__ import print_function

from logilab.common import modutils, Execute as spawn
from logilab.common.astutils import *
import os.path

MY_DICT = {}


def global_access(key, val):
    """function test"""
    local = 1
    MY_DICT[key] = val
    for i in val:
        if i:
            del MY_DICT[i]
            continue
        else:
            break
    else:
        print('!!!')

class YO:
    """hehe"""
    a=1
    def __init__(self):
        try:
            self.yo = 1
        except ValueError as ex:
            pass
        except (NameError, TypeError):
            raise XXXError()
        except:
            raise

#print('*****>',YO.__dict__)
class YOUPI(YO):
    class_attr = None

    def __init__(self):
        self.member = None

    def method(self):
        """method test"""
        global MY_DICT
        try:
            MY_DICT = {}
            local = None
            autre = [a for a, b in MY_DICT if b]
            if b in autre:
                print('yo', end=' ')
            elif a in autre:
                print('hehe')
            global_access(local, val=autre)
        finally:
            return local

    def static_method():
        """static method test"""
        assert MY_DICT, '???'
    static_method = staticmethod(static_method)

    def class_method(cls):
        """class method test"""
        exec(a, b)
    class_method = classmethod(class_method)
