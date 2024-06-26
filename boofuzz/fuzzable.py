"""Base class for all fuzzable types."""
from __future__ import annotations

import itertools
import os
import typing

from boofuzz.mutation import Mutation
from .mutation_context import MutationContext
from .protocol_session_reference import ProtocolSessionReference

if typing.TYPE_CHECKING:
    from boofuzz.blocks.request import Request


class Fuzzable:
    """Parent class for all primitives and blocks.

    When making new fuzzable types, one will typically override :meth:`mutations` 
    and/or :meth:`encode`.

    :meth:`mutations` is a generator function yielding mutations, typically of type bytes.

    :meth:`encode` is a function that takes a value and encodes it. 
        The value comes from :meth:`mutations` or `default_value`. 
    :class:`FuzzableBlock <boofuzz.FuzzableBlock>` types can also encode the data generated 
        by child nodes.

    Implementors may also want to override :meth:`num_mutations` -- the default implementation 
    manually exhausts :meth:`mutations` to get a number.

    The rest of the methods are used by boofuzz to handle fuzzing and are typically not overridden.

    :type name: str, optional
    :param name: Name, for referencing later. 
        Names should always be provided, but if not, a default name will be given,
        defaults to None
    :type default_value: Any, optional
    :param default_value: Value used when the element is not being fuzzed.
        Should typically represent a valid value.
        Can be a static value, or a ReferenceValueTestCaseSession, defaults to None
    :type fuzzable: bool, optional
    :param fuzzable: Enable fuzzing of this primitive, defaults to True
    :type fuzz_values: list, optional
    :param fuzz_values: List of custom fuzz values to add to the normal mutations, defaults to None
    """

    name_counter = 0

    def __init__(self,
                 name=None,
                 default_value=None, fuzzable=True, fuzz_values=None,
                 *args, **kwargs):
        self._fuzzable = fuzzable
        self._name = name
        self._default_value = default_value
        self._context_path = ""
        self._request = None
        self._halt_mutations = False
        if fuzz_values is None:
            fuzz_values = list()
        self._fuzz_values = fuzz_values

        self.primitive_seed = None
        # Used to generate different random values for each same-type primitive in the same request

        if self._name is None:
            Fuzzable.name_counter += 1
            self._name = f"{type(self).__name__}{Fuzzable.name_counter}"

    @property
    def fuzzable(self):
        """If False, this element should not be mutated in normal fuzzing."""
        return self._fuzzable

    @property
    def name(self):
        """Element name, should be unique for each instance.

        :rtype: str
        """
        return self._name

    @property
    def qualified_name(self):
        """Dot-delimited name that describes the request name and the path to the element 
        within the request.

        Example: "request1.block1.block2.node1"

        """
        return ".".join(s for s in (self._context_path, self.name) if s != "")

    @property
    def context_path(self):
        """Dot-delimited string that describes the path up to this element.
        Configured after the object is attached
        to a Request."""
        if not hasattr(self, "_context_path"):
            self._context_path = None
        return self._context_path

    @context_path.setter
    def context_path(self, x):
        self._context_path = x

    @property
    def request(self) -> Request | None:
        """Reference to the Request to which this object is attached."""
        if not hasattr(self, "_request"):
            self._request = None
        return self._request

    @request.setter
    def request(self, x):
        self._request = x

    def stop_mutations(self):
        """Stop yielding mutations on the currently running :py:meth:`mutations` call.

        Used by boofuzz to stop fuzzing an element when it's already caused several failures.

        Returns:
            NoneType: None
        """
        self._halt_mutations = True

    def original_value(self, test_case_context=None):
        """Original, non-mutated value of element.

        Args:
            test_case_context (ProtocolSession): Used to resolve ReferenceValueTestCaseSession type default values.

        Returns:
        """
        if isinstance(self._default_value, ProtocolSessionReference):
            if test_case_context is None:
                return self._default_value.default_value
            else:
                return test_case_context.session_variables[self._default_value.name]
        else:
            return self._default_value

    def get_mutations(self):
        """Iterate mutations. Used by boofuzz framework.

        Yields:
            list of Mutation: Mutations

        """
        try:
            if not self.fuzzable:
                return
            index = 0
            # Concatenate the seed of the session and the name of the element
            # to generate a unique seed for each element
            self.primitive_seed = self.request.parent_session.seed + self.qualified_name
            for value in itertools.chain(self.mutations(self.original_value()), self._fuzz_values):
                if self._halt_mutations:
                    self._halt_mutations = False
                    return
                if isinstance(value, list):
                    yield value
                elif isinstance(value, Mutation):
                    yield [value]
                else:
                    yield [Mutation(value=value, qualified_name=self.qualified_name, index=index)]
                    index += 1
        finally:
            self._halt_mutations = False
            # in case stop_mutations is called when mutations were exhausted anyway

    def render(self, mutation_context=None):
        """Render after applying mutation, if applicable.
        :type mutation_context: MutationContext
        """
        return self.encode(
            value=self.get_value(mutation_context=mutation_context),
            mutation_context=mutation_context)

    def get_num_mutations(self):
        """
        Get the number of mutations for this element.
        """
        return self.num_mutations(default_value=
                                  self.original_value(test_case_context=None)) + len(self._fuzz_values)

    def get_value(self, mutation_context=None):
        """Helper method to get the currently applicable value.

        This is either the default value, or the active mutation value 
        as dictated by mutation_context.

        Args:
            mutation_context (MutationContext):

        Returns:

        """
        if mutation_context is None:
            mutation_context = MutationContext()
        if self.qualified_name in mutation_context.mutations:
            mutation = mutation_context.mutations[self.qualified_name]
            if callable(mutation.value):
                value = mutation.value(
                    self.original_value(test_case_context=mutation_context.protocol_session))
            else:
                value = mutation.value
        else:
            value = self.original_value(test_case_context=mutation_context.protocol_session)

        return value

    def mutations(self, default_value):
        """Generator to yield mutation values for this element.

        Values are either plain values or callable functions that take a "default value"
        and mutate it.
        Functions are used when the default or "normal" value influences the fuzzed value. 
        Functions are used because the "normal" value is sometimes dynamic and not known
        at the time of generation.

        Each mutation should be a pre-rendered value. 
        That is, it must be suitable to pass to encode().

        Default: Empty iterator.

        Args:
            default_value:
        """
        return
        yield

    def encode(self, value, mutation_context):
        """Takes a value and encodes/renders/serializes it to a bytes (byte string).

        Optional if mutations() yields bytes.

        Example: Yield strings with mutations() and encode them to UTF-8 using encode().

        Default behavior: Return value.

        Args:
            value: Value to encode. Type should match the type yielded by mutations()
            mutation_context (MutationContext): Context for current mutation, if any.


        Returns:
            bytes: Encoded/serialized value.
        """
        return value

    def num_mutations(self, default_value):
        """Return the total number of mutations for this element (not counting "fuzz_values").

        Default implementation exhausts the mutations() generator, which is inefficient.
        Override if you can provide a value more efficiently, or if exhausting the mutations()
        generator has side effects.

        Args:
            default_value: Use if number of mutations depends on the default value.
                Provided by FuzzableWrapper.
                Note: It is generally good behavior to have a consistent number of mutations
                for a given default value length.

        Returns:
            int: Number of mutated forms this primitive can take
        """
        return sum(1 for _ in self.mutations(default_value=default_value))

    def random_generation(self):
        """
        Abstract methode to generate random values for the element.
        """
        raise NotImplementedError("This method is abstract")

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} {repr(self.original_value(test_case_context=None))}>"

    def __len__(self):
        """Length of field. May vary if mutate() changes the length.

        Returns:
            int: Length of element (length of mutated element if mutated).
        """
        return len(self.render(MutationContext()))

    def __bool__(self):
        """Make sure instances evaluate to True even if __len__ is zero.

        Design Note: Exists in case some wise guy uses `if my_element:` to
        check for null value.

        Returns:
            bool: True
        """
        return True
