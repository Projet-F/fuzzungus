"""
:mod:`boofuzz.primitives.bytes`
================================
This module contains the implementation of the Bytes primitive.
"""
from collections.abc import ByteString
import os
import itertools
import math
import random

from funcy import compose
from .base_primitive import BasePrimitive


class Bytes(BasePrimitive):
    """Primitive that fuzzes a binary byte string with arbitrary length.

    :type name: str, optional
    :param name: Name, for referencing later. Names should always be provided, but if not, *
        a default name will be given, defaults to None
    :type default_value: bytes, optional
    :param default_value: Value used when the element is not being fuzzed - should typically
        represent a valid value, defaults to b""
    :type size: int, optional
    :param size: Deprecated, kept for retrocompatibility, use min_len and max_len.
        Static size of this field, leave None for dynamic, defaults to None
    :type padding: chr, optional
    :param padding: Value to use as padding to fill static field size, defaults to b"\\x00"
    :type min_len: int, optional
    :param min_len: Minimum string length, defaults to 0
    :type max_len: int, optional
    :param max_len: Maximum string length, defaults to None
    :type max_element_by_round: int, optional
    :param max_element_by_round: Maximum number of elements to generate by round, defaults to 100
        Truncate seclists if necessary    
    :type fuzzable: bool, optional
    :param fuzzable: Enable/disable fuzzing of this primitive, defaults to true
    :type use_long_bytes: bool, optional
    :param use_long_bytes: Enable/disable the use of long bytes, defaults to True
    :type use_default_value: bool, optional
    :param use_default_value: Enable/disable the use of the default value, defaults to True
    """

    # from https://en.wikipedia.org/wiki/Magic_number_(programming)#Magic_debug_values
    _magic_debug_values = [
        b"\x00",
        b"\x01",
        b"\x80",
        b"\xa5",
        b"\xFF",
        b"\x01\x00",
        b"\x00\x01",
        b'\xba\xd2""',
        b"\x7F\xFF",
        b"\xFF\x7F",
        b"\xFE\xFF",
        b"\xFF\xFE",
        b"\r\x15\xea^",
        b"\x00\x00\x81#",
        b"\xb1k\x00\xb5",
        b"\xba\xad\xf0\r",
        b"\x8b\xad\xf0\r",
        b"\xde\xad\xf0\r",
        b"\xca\xfe\xd0\r",
        b"\x00\x00\x00\x01",
        b"\x01\x00\x00\x00",
        b"\x7F\xFF\xFF\xFF",
        b"\xFF\xFF\xFF\x7F",
        b"\xFE\xFF\xFF\xFF",
        b"\xFF\xFF\xFF\xFE",
        b"\x00\xfa\xca\xde",
        b"\x1b\xad\xb0\x02",
        b"\xa5\xa5\xa5\xa5",
        b"\xab\xab\xab\xab",
        b"\xab\xad\xba\xbe",
        b"\xab\xba\xba\xbe",
        b"\xab\xad\xca\xfe",
        b"\xba\xaa\xaa\xad",
        b"\xba\xdd\xca\xfe",
        b"\xbb\xad\xbe\xef",
        b"\xbe\xef\xca\xce",
        b"\xc0\x00\x10\xff",
        b"\xca\xfe\xba\xbe",
        b"\xca\xfe\xfe\xed",
        b"\xcc\xcc\xcc\xcc",
        b"\xcd\xcd\xcd\xcd",
        b"\xdd\xdd\xdd\xdd",
        b"\xde\xad\x10\xcc",
        b"\xde\xad\xba\xbe",
        b"\xde\xad\xbe\xef",
        b"\xde\xad\xca\xfe",
        b"\xde\xad\xc0\xde",
        b"\xde\xad\xfa\x11",
        b"\xde\xfe\xc8\xed",
        b"\xde\xad\xde\xad",
        b"\xeb\xeb\xeb\xeb",
        b"\xfa\xde\xde\xad",
        b"\xfd\xfd\xfd\xfd",
        b"\xfe\xe1\xde\xad",
        b"\xfe\xed\xfa\xce",
        b"\xfe\xee\xfe\xee",
        b"\xba\xdb\xad\xba\xdb\xad",
        b"\xba\xdc\x0f\xfe\xe0\xdd\xf0\r",
    ]

    _long_bytes_lengths = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 32768, 0xFFFF]
    _long_bytes_deltas = [-2, -1, 0, 1, 2]
    _extra_long_bytes_lengths = [99999, 100000, 500000, 1000000]

    _default_value_multipliers = [2, 10, 100]

    def __init__(
        self,
        *args,
        name: str = None,
        default_value: bytes = b"",
        padding: bytes = b"\x00",
        size: int = None,
        min_len:int=0,
        max_len:int=1000,
        use_long_bytes:bool=True,
        use_default_value: bool = True,
        **kwargs
    ):
        # Check types
        if not isinstance(default_value, ByteString):
            raise TypeError("default_value of Bytes must be of ByteString type")
        if not isinstance(padding, ByteString):
            raise TypeError("padding of Bytes must be of ByteString type")

        super().__init__(name=name, default_value=default_value, *args, **kwargs)

        self.min_len = min_len
        self.max_len = max_len
        # Keeping self.size for retrocompatibility
        self.size = size
        self.random_indices = {}
        self.use_long_bytes=use_long_bytes
        self.use_default_value = use_default_value
        if self.size is not None:
            self.max_len = self.size
            self.min_len = self.size

        self.padding = padding


    def mutations(self, default_value):
        """
        Generate mutations :

        * If the round_type is "library", do so using the variables and functions yielded by 
            _iterate_fuzz_cases.
            * If the element is callable, calls it.
            * If not, returns the element.
            * Checks for the size each time.
        * Else, if round_type is random_mutation, flip random bits in the value.
        * Else, if round_type is random_generation, generate random bytes of random size.

        :param default_value:
        :return: A generator of mutated values
        """
        if self.request.parent_session.round_type == "library" :
            for fuzz_value in itertools.islice(itertools.chain(
                self._yield_variable_mutations(default_value),
                self._yield_long_magic_debug_values(),
                self._yield_from_file(),
            ), self.num_library_elements):
                if callable(fuzz_value):
                    yield compose(self._adjust_mutation_for_size, fuzz_value)
                else:
                    yield self._adjust_mutation_for_size(fuzz_value=fuzz_value)
        if self.request.parent_session.round_type == "random_mutation" :
            # Get all the values from the itertools.chain
            library = list(itertools.chain(
                self._yield_variable_mutations(default_value),
                self._yield_long_magic_debug_values(),
                self._yield_from_file(),
            ))

            # If the seed index (the round number) is less than or equal to the max_rounds_mutation,
            # mutate the character
            if self.request.parent_session.seed_index < self.max_rounds_mutation:
                # Get the seedth value of the itertools.chain
                # seed isn't only used to generate random, but also as an index
                current_val = self.get_nth(library, self.request.parent_session.seed_index)

                # If the current value is not None, yield the mutated character.
                # If the current value is not None, yield the mutated character.
                # If it is None, do nothing.
                random.seed(self.primitive_seed)
                if current_val is not None:
                    for data in self._mutate_bytes(current_val):
                        yield self._adjust_mutation_for_size(data)

        if self.request.parent_session.round_type == "random_generation":
            random.seed(self.primitive_seed)
            for _ in range(self.num_random_generations):
                yield self.random_generation()

    def _adjust_mutation_for_size(self, fuzz_value:bytes):
        """
        If the fuzz_value is too long, cut it. If it is too short, pad it.

        :type fuzz_value: bytes
        :param fuzz_value: The fuzz_value to adjust
        :return: The adjusted fuzz_value
        """
        if len(fuzz_value) > self.max_len:
            fuzz_value = fuzz_value[: self.max_len]

        if len(fuzz_value) < self.min_len:
            fuzz_value = fuzz_value + self.padding * (self.min_len - len(fuzz_value))

        return fuzz_value

    def _yield_variable_mutations(self, default_value):
        """
        Yield variable mutations of the default value if use_default_value is True.
        """
        if self.use_default_value:
            for length in self._default_value_multipliers:
                value = default_value * length
                yield value
                if self.max_len is not None and len(value) >= self.max_len:
                    break
                yield value
                if self.max_len is not None and len(value) >= self.max_len:
                    break
        else :
            yield default_value

    def _yield_from_file(self):
        """
        Load fuzz library from file.         
        Yields lines from file that are not comments or empty.
        Ignore if seclist_path is empty.

        Raises : FileNotFoundError if file not found.
        """
        if self.seclist_path :
            abs_filepath = self._get_seclist_abs_path()

            # Open file and yield lines that are not comments or empty
            try:
                with open(abs_filepath, "r", encoding="ascii") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            yield line.encode()
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File not found: {abs_filepath}") from exc

    def _yield_long_magic_debug_values(self):
        """
        For each value in magic_debug_values, yield a number of selectively chosen bytes lengths.
        Ignore if use_long_bytes is False.
        """
        if self.use_long_bytes:
            for sequence in self._magic_debug_values:
                if len(sequence)!=0:
                    
                    for size in [
                        length + delta
                        for length, delta
                        in itertools.product(self._long_bytes_lengths, self._long_bytes_deltas)
                    ]:
                        if self.max_len is None or size <= self.max_len:
                            data = sequence * math.ceil(size / len(sequence))
                            yield data[:size]
                        else:
                            break

                    for size in self._extra_long_bytes_lengths:
                        if self.max_len is None or size <= self.max_len:
                            data = sequence * math.ceil(size / len(sequence))
                            yield data[:size]
                        else:
                            break

                    if self.max_len is not None:
                        data = sequence * math.ceil(self.max_len / len(sequence))
                        yield data

    def _mutate_bytes(self, bytes_to_mutate: bytes) :
        for _ in range(self.num_random_mutations):
            if bytes_to_mutate == "":
                yield bytes_to_mutate

            # Convert the byte string to a list of bits
            bit_list = list(format(int.from_bytes(bytes_to_mutate, 'big'), '08b'))

            # Choose a random bit to flip
            bit_to_flip = random.randint(0, len(bit_list) - 1)

            # Flip the chosen bit
            bit_list[bit_to_flip] = '0' if bit_list[bit_to_flip] == '1' else '1'

            # Convert the bit list back to a byte string
            bytes_to_mutate = int(''.join(bit_list), 2).to_bytes(len(bytes_to_mutate), 'big')

            # Replace the character at the chosen position with the new character
            yield bytes_to_mutate

    def num_mutations(self, default_value) -> int:
        """
        Calculate and return the total number of mutations for this individual primitive.

        @rtype:  int
        @return: Number of mutated forms this primitive can take
        :param default_value:
        """

        if self.request.parent_session.round_type == "library" :
            return len(
                list(
                    itertools.islice(
                        itertools.chain(
                            self._yield_variable_mutations(default_value),
                            self._yield_long_magic_debug_values(),
                            self._yield_from_file(),
                        ),
                        self.num_library_elements
                    )
                )
            )

        if self.request.parent_session.round_type == "random_mutation":
            return self.num_random_mutations

        if self.request.parent_session.round_type == "random_generation":
            return self.num_random_generations

    def encode(self, value, mutation_context):
        if value is None:
            value = b""
        return value

    def random_generation(self):
        """
        Generate random bytes, of a random size between self.min_len and self.max_len.
        """
        size = random.randint(self.min_len, self.max_len)
        return os.urandom(size)
