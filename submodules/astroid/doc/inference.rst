.. _inference:

Inference Introduction
======================

What/where is 'inference' ?
---------------------------


The inference is a mechanism through which *astroid* tries to interpret
statically your Python code.

How does it work ?
------------------

The magic is handled by :meth:`NodeNG.infer` method.
*astroid* usually provides inference support for various Python primitives,
such as protocols and statements, but it can also be enriched
via `inference transforms`.

In both cases the :meth:`infer` must return a *generator* which iterates
through the various *values* the node could take.

In some case the value yielded will not be a node found in the AST of the node
but an instance of a special inference class such as :class:`Uninferable`,
or :class:`Instance`.

Namely, the special singleton :obj:`Uninferable()` is yielded when the inference reaches
a point where it can't follow the code and is so unable to guess a value; and
instances of the :class:`Instance` class are yielded when the current node is
inferred to be an instance of some known class.
