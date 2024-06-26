.. _primitives:

Primitives
==========

A Sulley Primitive has an interface partially defined by class `BasePrimitive`.
The interface consists importantly of:

 * Mutation method.
 * Rendering method.
 * Num-mutations method to get total mutation count.
 * Reset method to reset the primitive to non-mutated state.
 * A name property.
 * Support for reading length.

Most of these interface elements are shared by :ref:`blocks`.

BasePrimitive
-------------

.. warning::

    When using primitives (or developing new ones), keep in mind the parameters available in the BasePrimitive :)

.. autoclass:: boofuzz.BasePrimitive
    :members:
    :undoc-members:
    :show-inheritance:

BitField
--------
.. autoclass:: boofuzz.BitField
    :members:
    :undoc-members:
    :show-inheritance:

Byte
----
.. autoclass:: boofuzz.Byte
    :members:
    :undoc-members:
    :show-inheritance:

Bytes
-----
.. autoclass:: boofuzz.Bytes
    :members:
    :undoc-members:
    :show-inheritance:

Delim
-----
.. autoclass:: boofuzz.Delim
    :members:
    :undoc-members:
    :show-inheritance:

DWord
-----
.. autoclass:: boofuzz.DWord
    :members:
    :undoc-members:
    :show-inheritance:

FromFile
--------
.. autoclass:: boofuzz.FromFile
    :members:
    :undoc-members:
    :show-inheritance:

Group
-----
.. autoclass:: boofuzz.Group
    :members:
    :undoc-members:
    :show-inheritance:

Mirror
------
.. autoclass:: boofuzz.Mirror
    :members:
    :undoc-members:
    :show-inheritance:

MultipleDefault
---------------

.. autoclass:: boofuzz.MultipleDefault
    :members:
    :undoc-members:
    :show-inheritance:

QWord
-----
.. autoclass:: boofuzz.QWord
    :members:
    :undoc-members:
    :show-inheritance:

RandomData
----------
.. autoclass:: boofuzz.RandomData
    :members:
    :undoc-members:
    :show-inheritance:

Simple
------
.. autoclass:: boofuzz.Simple
    :members:
    :undoc-members:
    :show-inheritance:

Static
------
.. autoclass:: boofuzz.Static
    :members:
    :undoc-members:
    :show-inheritance:

String
------
.. autoclass:: boofuzz.String
    :members:
    :undoc-members:
    :show-inheritance:

Word
----
.. autoclass:: boofuzz.Word
    :members:
    :undoc-members:
    :show-inheritance: