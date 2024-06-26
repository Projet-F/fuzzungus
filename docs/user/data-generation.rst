.. _data-generation:

Data Generation
================

Boofuzz wasn't consistent with data generation for each of it's primitives. 
Sometimes it was yielding elements of an internal class library, sometimes multiplying a seed, and sometimes mutating data.

We deployed a consistent data generation strategy across all primitives, following three modes.

Data Generation Modes
---------------------

Each primitives normally implements three modes of data generation :

- Library : The primitive will yield elements from a library of values, for which the composition is detailled in the :ref:`library` section.
- Random Mutation : The primitive will yield a defined number of recursively mutated values from an element of the library.
- Random Generation : The primitive will yield a defined number of randomly generated values.

The call to the apropiate mode is done by the `mutations` method of the primitive.

The choice of the mode is done directly in the Session, that possesses a `round_type` attribute that will be set successively to `library`, `random_mutation` and `random_generation`. It can be set manually at the beginning of a fuzzing section, in the configuration file, to the desired value.

The random is fixed for each primitive, with a seed set by the :ref:`session`. The seed is composed of : 

- A `seed_index` that can be set in the configuration file, that values 0 by default, and that will be incremented at each round.
- The `mutation_type`, merged with the `seed_index` in `session.fuzz_indefinitly` to get a unique seed for each round.
- The name of the primitive fuzzed, merged with the rest in `fuzzable.get_mutations` to get a unique seed for each primitives inside a round.

.. _library:

Library
-------

Some primitives contained a `_fuzz_library`, which was sort of an internal seclist. 
For each primitive, the elements of the library were moved : 

* In a seclist in `boofuzz/data/home_made_seclists/` for plain lines.
* With the long string seeds for lines that needed to be interpreted has python script, like `"/.*5000`.

Indeed, some primitives also contained some `_long_string_seeds` which were used to generate long strings. We standardized those in almost all primitives.

Currently, almost every primitive implements the library mode the same way, concatenating the following elements : 

* A seclist that can be passed as a parameter to the primitive. Fuzzungus now implements one of Boofuzz todos, which was a sane way to handle files.
    * To simpify the process of finding a good seclist for a primitive, we added the Seclist repo as a submodule, see :ref:`install` for more information.
    * The method used to read files raises an error if the file isn't found, and ignores empty lines and comments. 
    * The existence of the said file is checked at the initialization, to avoid errors during fuzzing.
* A list of long string seed, that are used to generate those arbitrary long strings.
* The default value and long strings generated from it.

Each of those three sources for the library have a corresponding parameter in the primitive constructor, to specify if they should be used or not.

Random Mutation
---------------

Each round of random mutation takes a different element from the library, obviously starting from the first one.
Each element is mutated a defined number of times, successively to get more and more mutated outputs, that are then yielded.

Two important parameters are used to define the total number of mutations round to do, and the number of mutations to perform on each element.

Random Generation
-----------------

Each round of random generation will generate a defined number of random values, that are then yielded. 
The specificity of the generation for each primitive is detailled in the method `random_generation` of the primitive.
Just know that the generation is done accordingly to the primitive type, for exemple generating unicode code positions for a string primitive, that are then encoded, or random bytes for a byte primitive.

Example Fuzzing Session
-----------------------

Below is an example of how each round of fuzzing could look like, with a library of elements, and a defined number of mutations and generations.

.. digraph:: fuzz_indefinitely

    node[shape=record]
    size="20"
    nodesep=1

    rankdir=LR;  // Left to Right layout

    subgraph cluster_library {
        color="blue";
        label="Library";
        L0 [label="L[0]..."];
        Ln [label="L[n]"];

        L0 -> Ln;
    }

    subgraph cluster_mutation {
        color="red";
        label="Mutation";
        subgraph cluster_mutation_0 {
            label="seed=0";
            m0_start [label="m(L[0],0)"];
            m0_end [label="m(L[0],k)"];

            m0_start -> m0_end;
        }
        subgraph cluster_mutation_N {
            label="seed=1";
            mN_start [label="m(L[n],0)"];
            mN_end [label="m(L[n],k)"];

            mN_start -> mN_end;
        }

        m0_end -> mN_start;
    }

    subgraph cluster_generation {
        color="green";
        label="Generation";
        g0 [label="g(0) x j"];
        g1 [label="g(1) x j"];
        
        g0 -> g1;
    }

    Ln -> m0_start 
    
    mN_end -> g0;




With :math:`m(obj, index)` the mutation function, and :math:`g(index)` the generation function :

1. Library : Each library element is sent to the target.
2. Random Mutation: Each library element is mutated :math:`k` times.
3. Random generation : With a different seed for each round, :math:`j` random elements are generated. 