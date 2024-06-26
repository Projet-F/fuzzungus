.. _blocks:

Blocks
======

Request
-------

The Request class has push and pop methods for creating it.
Whenever a new Block is opened/started, it is pushed onto the "block stack".
Note that this is different than the "stack".
When a Block is closed, it is popped.

When the Request is assembled in the fuzz definition, its stack should be empty.
To accomplish this, all blocks should be closed.

.. autoclass:: boofuzz.Request
   :members:
   :undoc-members:
   :show-inheritance:

Block
-----
.. autoclass:: boofuzz.Block
   :members:
   :undoc-members:
   :show-inheritance:

Checksum
--------

Sulley's Checksum class creates a block that calculates the checksum of another block.

Algorithms
^^^^^^^^^^

Checksum contains only the Sulley block logic for a checksum, not specific
algorithm implementations.
Algorithms are implemented with a library or a free function.

Recursion
^^^^^^^^^

To enable a checksum to be calculated over its parent block, it is necessary
to account for recursion.
This is done with a recursion flag.
When Checksum renders itself for the sake of calculations, it will set a
recursion flag on itself.
Then, when the parent block again renders the Checksum, Checksum will check its
own recursion flag and return its default value.

Note: To avoid recursion problems with Size, it is important that Checksum's
length method not call render on itself.

UDP
^^^

UDP is special in that it is computed over a pseudo-header, including selected
fields from IPv4 and the entire UDP header and payload.
The IPv4 fields are:

 * IPv4 Source Address
 * IPv4 Destination Address
 * Protocol (should always be UDP)
 * Length of UDP header+payload

Note that these fields do not themselves need to be individually fuzzed, since
fuzzing any of them would result in a bad checksum -- and a bad checksum can be
checked by fuzzing the checksum field itself.

Designs considered:

 1. Passing a reference to the IPv4 Sulley Block and navigating to its children.
 2. Passing source and destination addresses directly to the Checksum
    constructor.
 3. Passing references to the source and destination Sulley Blocks into the
    Checksum constructor.
    
Option 1 was rejected as being too involved.
It would need to know the structure of the IPv4 Sulley Block, which would
result in complexity and possibly duplicated information.

Option 2 was rejected as inferior to 1 and 3.
With option 2, when the IPv4 source or destination address is being fuzzed,
the UDP checksum will automatically start failing.
This could draw attention away from the IPv4 src/dst fields for the sake of
fuzzing.

With option 3, when the IPv4 src/dst fields are being fuzzed, the UDP checksum
will still pass.
Furthermore, taking a reference to two Sulley Blocks is relatively easy.

Source Code
^^^^^^^^^^^

.. autoclass:: boofuzz.Checksum
   :members:
   :undoc-members:
   :show-inheritance:

Repeat
------

.. autoclass:: boofuzz.Repeat
   :members:
   :undoc-members:
   :show-inheritance:

Size
----

The Size class creates a block that calculates the size of another block.

Calculation
^^^^^^^^^^^
To calculate the size of its target block, Size simply calls `len()` on the
target (all Sulley Primitives must support `__len__()`).

Design Considerations
^^^^^^^^^^^^^^^^^^^^^^
Size was originally calculated by rendering the target block, or using
callbacks to wait for it to get rendered.
This resulted in dependency issues if a block contained both Size and Checksum
primitives, or in blocks that referenced each other.
Checksum naturally depends on Size's value, but if Size depends on Checksum's
value, we have a recursion problem.

The current design is motivated by the fact that, in reality, Size does not
depend on Checksum's value. Depending on the length method rather than
rendering more closely matches reality.

.. autoclass:: boofuzz.Size
   :members:
   :undoc-members:
   :show-inheritance:

Aligned
-------

.. autoclass:: boofuzz.Aligned
   :members:
   :undoc-members:
   :show-inheritance:
