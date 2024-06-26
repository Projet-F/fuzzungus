Fuzzungus: Advanced Network Protocol Fuzzing
============================================

.. image:: ./_static/media/badge.svg
    :alt: Build Status
.. image:: ./_static/media/badge_doc.svg
    :alt: Documentation Status
.. image:: ./_static/media/boofuzz.svg
.. image:: ./_static/media/style-black.svg

Fuzzungus is a fork of the `Boofuzz`_ framework, itself a fork and the successor of to the venerable `Sulley`_ fuzzing
framework. Fuzzungus was created as part of a Safran Electronics & Defense project.

Why?
----

Boofuzz was lacking a lot of the features needed to fuzz aerospace protocols. By forking `Boofuzz`_, the goal was to
be able to easily add them without having to undergo the code review of Boofuzz maintainers, to speed up the development.

This project won't be maintained much further, excepted some minor fixes and updates by the Safran Electronics & Defense 
Red Team, so feel free to fork it and make it your own, or, if you happen to be one of the maintainers of Boofuzz, to
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

In the continuity of Boofuzz, Fuzzungus is also named after a character from Monsters Inc. 
This time, it's Fungus, the assistant of the villain Randall Boggs, just because it's a funny name.

.. figure:: ../artwork/fungus-picture.png
   :alt: Jeff Fungus from Monsters Inc

   Jeff Fungus from Monsters Inc

Installation
------------

Boofuzz was installable as a Python library through `pip`, but it isn't the case of Fuzzungus, that has to be installed through the source code.
See :ref:`install` for advanced and detailed instructions.


.. toctree::
    :caption: User Guide
    :maxdepth: 2

    user/install
    user/quickstart
    user/contributing


.. toctree::
    :caption: API Documentation
    :maxdepth: 2

    user/main
    user/callgraph
    user/packages
    source/Session
    source/Target
    user/connections
    user/monitors
    user/logging
    user/other-modules
    user/callbacks

.. toctree::
    :caption: Protocol Definition
    :maxdepth: 2

    user/protocol-overview
    user/blocks
    user/primitives
    user/data-generation
    user/session-configuration

.. toctree::
    :caption: Changelog
    :maxdepth: 1

    user/changelog

Contributions
-------------

Pull requests are welcome, as boofuzz is actively maintained (at the
time of this writing ;)). See :ref:`contributing`.

.. _community:

Community
---------

For questions that take the form of “How do I… with boofuzz?” or “I got
this error with boofuzz, why?”, consider posting your question on Stack
Overflow. Make sure to use the ``fuzzing`` tag.

If you’ve found a bug, or have an idea/suggestion/request, file an issue
here on GitHub.

For other questions, check out boofuzz on `gitter`_ or `Google Groups`_.

For updates, follow `@b00fuzz`_ on Twitter.

.. _Sulley: https://github.com/OpenRCE/sulley
.. _Boofuzz: https://github.com/jtpereyda/boofuzz
.. _Google Groups: https://groups.google.com/d/forum/boofuzz
.. _gitter: https://gitter.im/jtpereyda/boofuzz
.. _@b00fuzz: https://twitter.com/b00fuzz
.. _boofuzz-ftp: https://github.com/jtpereyda/boofuzz-ftp
.. _boofuzz-http: https://github.com/jtpereyda/boofuzz-http


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
