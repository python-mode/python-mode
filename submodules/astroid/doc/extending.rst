Extending astroid syntax tree
=============================

Sometimes astroid will miss some potentially important information
you may wish it supported instead, for instance with the libraries that rely
on dynamic features of the language. In some other cases, you may
want to customize the way inference works, for instance to explain **astroid**
that calls to `collections.namedtuple` are returning a class with some known
attributes.


Modifications in the AST are possible in a couple of ways.

AST transforms
^^^^^^^^^^^^^^

**astroid** has support for AST transformations, which given a node,
should return either the same node but modified, or a completely new node.

The transform functions needs to be registered with the underlying manager,
that is, a class that **astroid** uses internally for all things configuration
related. You can access the manager using `astroid.MANAGER`.

The transform functions need to receive three parameters, with the third one
being optional:

* the type of the node for which the transform will be applied

* the transform function itself

* optionally, but strongly recommended, a transform predicate function.
  This function receives the node as an argument and it is expected to
  return a boolean specifying if the transform should be applied to this node
  or not.

AST transforms - example
------------------------

Let's see some examples!

Say that we love the new Python 3.6 feature called ``f-strings``, you might have
heard of them and now you want to use them in your Python 3.6+ project as well.

So instead of ``"your name is {}".format(name)"`` we'd want to rewrite this to
``f"your name is {name}"``.

One thing you could do with astroid is that you can rewrite partially a tree
and then dump it back on disk to get the new modifications. Let's see an
example in which we rewrite our code so that instead of using ``.format()`` we'll
use f-strings instead.

While there are some technicalities to be aware of, such as the fact that
astroid is an AST (abstract syntax tree), while for code round-tripping you
might want a CST instead (concrete syntax tree), for the purpose of this example
we'll just consider all the round-trip edge cases as being irrelevant.

First of all, let's write a simple function that receives a node and returns
the same node unmodified::

    def format_to_fstring_transform(node):
        return node

    astroid.MANAGER.register_transform(...)


For the registration of the transform, we are most likely interested in registering
it for ``astroid.Call``, which is the node for function calls, so this now becomes::

    def format_to_fstring_transform(node):
        return node

    astroid.MANAGER.register_transform(
        astroid.Call,
        format_to_fstring_transform,
    )

The next step would be to do the actual transformation, but before dwelving
into that, let's see some important concepts that nodes in astroid have:

* they have a parent. Everytime we build a node, we have to provide a parent

* most of the time they have a line number and a column offset as well

* a node might also have children that are nodes as well. You can check what
  a node needs if you access its ``_astroid_fields``, ``_other_fields``, ``_other_other_fields``
  properties. They are all tuples of strings, where the strings depicts attribute names.
  The first one is going to contain attributes that are nodes (so basically children
  of a node), the second one is going to contain non-AST objects (such as strings or
  other objects), while the third one can contain both AST and non-AST objects.

When instantiating a node, the non-AST parameters are usually passed via the
constructor, while the AST parameters are provided via the ``postinit()`` method.
The only exception is that the parent is also passed via the constructor.
Instantiating a new node might look as in::

    new_node = FunctionDef(
        name='my_new_function',
        doc='the docstring of this function',
        lineno=3,
        col_offset=0,
        parent=the_parent_of_this_function,
    )
    new_node.postinit(
        args=args,
        body=body,
        returns=returns,
    )


Now, with this knowledge, let's see how our transform might look::


    def format_to_fstring_transform(node):
        f_string_node = astroid.JoinedStr(
            lineno=node.lineno,
            col_offset=node.col_offset,
            parent=node.parent,
         )
         formatted_value_node = astroid.FormattedValue(
            lineno=node.lineno,
            col_offset=node.col_offset,
            parent=node.parent,
         )
         new_node.postinit(value=node.args[0])

         # Need to extract the part of the string that doesn't
         # have the formatting placeholders
         string = extract_string_without_placeholder(node.func.expr)

         f_string_node.postinit(values=[string, f_string_node])
         return new_node

    astroid.MANAGER.register_transform(
        astroid.Call,
        format_to_fstring_transform,
    )


There are a couple of things going on, so let's see what we did:

* ``JoinedStr`` is used to represent the f-string AST node.

  The catch is that the ``JoinedStr`` is formed out of the strings
  that don't contain a formatting placeholder, followed by the ``FormattedValue``
  nodes, which contain the f-strings formatting placeholders.

* ``node.args`` will hold a list of all the arguments passed in our function call,
  so ``node.args[0]`` will actually point to the name variable that we passed.

* ``node.func.expr`` will be the string that we use for formatting.

* We call ``postinit()`` with the value being the aforementioned name. This will result
  in the f-string being now complete.

You can now check to see if your transform did its job correctly by getting the
string representation of the node::

    from astroid import parse
    tree = parse('''
    "my name is {}".format(name)
    ''')
    print(tree.as_string())

The output should print ``f"my name is {name}"``, and that's how you do AST transformations
with astroid!

AST inference tip transforms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another interesting transform you can do with the AST is to provide the
so called ``inference tip``. **astroid** can be used as more than an AST library,
it also offers some basic support of inference, it can infer what names might
mean in a given context, it can be used to solve attributes in a highly complex
class hierarchy, etc. We call this mechanism generally ``inference`` throughout the
project.

An inference tip (or ``brain tip`` as another alias we might use), is a normal
transform that's only called when we try to infer a particular node.

Say for instance you want to infer the result of a particular function call. Here's
a way you'd setup an inference tip. As seen, you need to wrap the transform
with ``inference_tip``. Also it should receive an optional parameter ``context``,
which is the inference context that will be used for that particular block of inference,
and it is supposed to return an iterator::

    def infer_my_custom_call(call_node, context=None):
        # Do some transformation here
        return iter((new_node, ))


    MANAGER.register_transform(
        nodes.Call,
        inference_tip(infer_my_custom_call),
        _looks_like_my_custom_call,
    )

This transform is now going to be triggered whenever **astroid** figures out
a node for which the transform pattern should apply.


Module extender transforms
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another form of transforms is the module extender transform. This one
can be used to partially alter a module without going through the intricacies
of writing a transform that operates on AST nodes.

The module extender transform will add new nodes provided by the transform
function to the module that we want to extend.

To register a module extender transform, use the ``astroid.register_module_extender``
method. You'll need to pass a manager instance, the fully qualified name of the
module you want to extend and a transform function. The transform function
should not receive any parameters and it is expected to return an instance
of ``astroid.Module``.

Here's an example that might be useful::

    def my_custom_module():
        return astroid.parse('''
        class SomeClass:
            ...
        class SomeOtherClass:
            ...
        ''')

    register_module_extender(astroid.MANAGER, 'mymodule', my_custom_module)


Failed import hooks
^^^^^^^^^^^^^^^^^^^^

If you want to control the behaviour of astroid when it cannot import
some import, you can use ``MANAGER.register_failed_import_hook`` to register
a transform that's called whenever an import failed.

The transform receives the module name that failed and it is expected to
return an instance of :class:`astroid.Module`, otherwise it must raise
``AstroidBuildingError``, as seen in the following example::

    def failed_custom_import(modname):
        if modname != 'my_custom_module':
            # Don't know about this module
            raise AstroidBuildingError(modname=modname)
        return astroid.parse('''
        class ThisIsAFakeClass:
            pass
        ''')

    MANAGER.register_failed_import_hook(failed_custom_import)
