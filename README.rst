.. image:: ./artwork/fuzzungus-logo.png
    :width: 60%
    :alt: fuzzungus logo

Fuzzungus: Advanced Network Protocol Fuzzing
============================================

Fuzzungus is a fork of the `Boofuzz`_ framework, itself a fork and the successor of to the venerable `Sulley`_ fuzzing
framework. Fuzzungus was created as part of a Safran Electronics & Defense project.

Why?
----

Boofuzz was lacking a lot of the features needed to fuzz aerospace protocols. By forking `Boofuzz`_, the goal was to
be able to easily add them without having to undergo the code review of Boofuzz maintainers, to speed up the development.

This project won't be maintained much further, excepted some minor fixes if asked, so feel free to fork it and make it your own, or, if you happen to be one of the maintainers of Boofuzz, to
integrate the changes back into the main project. We would be happy to help you with that. 

Features
--------

Fuzzungus incorporates all the elements from Boofuzz :

-  Easy and quick data generation.
-  Instrumentation – AKA failure detection.
-  Target reset after failure.
-  Recording of test data.
-  Much easier install experience!
-  Support for arbitrary communications mediums.
-  Built-in support for serial fuzzing, ethernet- and IP-layer, UDP broadcast.
-  Better recording of test data -- consistent, thorough, clear.
-  Test result CSV export.
-  *Extensible* instrumentation/failure detection.
-  Far fewer bugs.

Fuzzungus also includes a number of new features:

- Refactored codebase of a number of modules to make it easier to understand and extend.
- Better configuration system
- Three generation modes (library, random mutation, and random generation)
- New primitives for data generation
- Great restart and continue on failure
- Timeout detection
- Full protocol sessions supports (multiple acks, fragmentation...)

.. figure:: ./artwork/fungus-picture.png
   :alt: Jeff Fungus from Monsters Inc

   Jeff Fungus from Monsters Inc

Installation
------------

See `INSTALL.rst`_ for advanced and detailed instructions.


Documentation
-------------

Go to the `docs/` repo to generate the documentation using `make html`.

