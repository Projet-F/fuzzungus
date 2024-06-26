"""External modules for string primitive."""
import itertools
import math
import random

from .base_primitive import BasePrimitive


class String(BasePrimitive):
    """
    Primitive that cycles through a library of "bad" strings.

    This class originally used a variable 'fuzz_library' containing a list of smart fuzz values
    global across all instances. The content was moved to a seclist file, removing the library variable.

    :type name: str, optional
    :param name: Name, for referencing later. Names should always be provided, but if not, a default
        name will be given, defaults to None
    :type default_value: str
    :param default_value: Value used when the element is not being fuzzed. Should typically
        represent a valid value.
    :type size: int, optional
    :param size: Deprecated. Static size of this field, leave None for dynamic, defaults to None. 
        Useless with min_len and max_len, kept for retrocompatibility.
    :type padding: chr, optional
    :param padding: Value to use as padding to fill static field size, defaults to "\\x00"
    :type encoding: str, optional
    :param encoding: String encoding, ex: utf_16_le for Microsoft Unicode, defaults to utf-8
    :type min_len: int, optional
    :param min_len: Minimum string length, defaults to None
    :type max_len: int, optional
    :type len_unit: str, optional
    :param len_unit: Unit used to calculate length, defaults to "bytes", can be "bytes" or "chars"
        If "chars", the length is checked in 'mutation', else in 'encode'.
    :param max_len: Maximum string length, defaults to None
    :type fuzzable: bool, optional
    :param fuzzable: Enable/disable fuzzing of this primitive, defaults to true
    :type seclist_path: string, optional
    :param seclist_path: Path to seclist file, defaults to "home_made_seclists/boofuzz.txt".
        Opened as utf-8.
    :type use_long_strings: bool, optional
    :param use_long_strings: Use built-in long strings, defaults to True
    :type use_default_value: bool, optional
    :param use_default_value: Use default value in the library, defaults to True
    :type num_random_generations: int, optional
    :param num_random_generations: Number of random string to generate, defaults to 50
    :type num_random_mutations: int, optional
    :param num_random_mutations: Number of mutations to generate, defaults to 40
    """

    # Has to be sorted to avoid duplicates
    long_string_seeds = [
        "C",
        "1",
        "<",
        ">",
        "'",
        '"',
        "/",
        "\\",
        "?",
        "=",
        "a=",
        "&",
        ".",
        ",",
        "(",
        ")",
        "]",
        "[",
        "%",
        "*",
        "-",
        "+",
        "{",
        "}",
        "\x14",
        "\x00",
        "\xFE",  # expands to 4 characters under utf1
        "\xFF",  # expands to 4 characters under utf1
        "%\xfe\xf0%\x01\xff",
        "/.",
        "/.:/",
        "/\\",
        "<>",
        "\r\n",
        "\xde\xad\xbe\xef",
    ]

    _long_string_lengths = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 32768, 0xFFFF]
    _long_string_deltas = [-2, -1, 0, 1, 2]
    _extra_long_string_lengths = [99999, 100000, 500000, 1000000]

    _default_value_multipliers = [2, 10, 100]

    _supported_encodings = ["utf-8", "utf-16", "utf-32", "ascii", "latin_1"]

    def __init__(
            self, *args, name=None, default_value="", size=None, padding=b"\x00", encoding="utf-8",
            min_len=0, max_len=1000, len_unit="bytes",
            use_long_strings=True, use_default_value=True, **kwargs
    ):
        super().__init__(name=name, default_value=default_value, *args, **kwargs)

        # Check encoding
        if encoding not in self._supported_encodings:
            raise ValueError(f"Unsupported encoding: {encoding}")

        self.min_len = min_len
        self.max_len = max_len
        if self.min_len is not None and self.max_len is not None and self.max_len < self.min_len:
            raise ValueError("max_len must be greater than or equal to min_len")
        self.len_unit = len_unit
        if self.len_unit not in ["bytes", "chars"]:
            raise ValueError("len_unit must be 'bytes' or 'chars'")
        # Keeping self.size for retrocompatibility
        self.size = size
        if self.size is not None:
            self.max_len = self.size
            self.min_len = self.size

        self.encoding = encoding
        self.padding = padding
        if isinstance(padding, str):
            self.padding = self.padding.encode(self.encoding)
        self._static_num_mutations = None
        self.random_indices = {}
        self.use_long_strings = use_long_strings
        self.use_default_value = use_default_value

        # We want constant random numbers to generate reproducible test cases
        local_random = random.Random(0)
        previous_length = 0
        # For every length add a random number of random indices to the random_indices dict.
        # Prevent duplicates by adding only indices in between previous_length and current length.
        for length in self._long_string_lengths:
            self.random_indices[length] = local_random.sample(
                range(previous_length, length),
                local_random.randint(1, self._long_string_lengths[0])
            )
            previous_length = length

    # Yielders
    def _yield_from_file(self):
        """
        Load fuzz library from file.         
        Yields lines from file that are not comments or empty.
        Ignore if seclist_path is empty.

        :raises : FileNotFoundError if file not found.
        """
        if self.seclist_path:
            abs_filepath = self._get_seclist_abs_path()

            # Open file and yield lines that are not comments or empty
            try:
                with open(abs_filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            yield line
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"File not found: {abs_filepath}") from exc

    def _yield_long_strings(self):
        """
        For every long string seed, yield a number of selectively chosen strings lengths. 
        Ignore if use_long_strings is False.
        """
        if self.use_long_strings:
            for sequence in self.long_string_seeds:
                for size in [
                    length + delta
                    for length, delta
                    in itertools.product(self._long_string_lengths, self._long_string_deltas)
                ]:
                    if self.max_len is None or size <= self.max_len:
                        data = sequence * math.ceil(size / len(sequence))
                        yield data[:size]
                    else:
                        break

                for size in self._extra_long_string_lengths:
                    if self.max_len is None or size <= self.max_len:
                        data = sequence * math.ceil(size / len(sequence))
                        yield data[:size]
                    else:
                        break

                if self.max_len is not None:
                    data = sequence * math.ceil(self.max_len / len(sequence))
                    yield data

            for size in self._long_string_lengths:
                if self.max_len is None or size <= self.max_len:
                    s = "D" * size
                    for loc in self.random_indices[size]:
                        # Replace character at loc with terminator
                        yield s[:loc] + "\x00" + s[loc + 1:]
                else:
                    break

    def _yield_variable_default_value(self, default_value):
        """
        Yield variable mutations of the default value if use_default_value is True.
        """
        if self.use_default_value:
            for length in self._default_value_multipliers:
                value = default_value * length

                yield value

    # Mutators
    def _adjust_mutation_for_size(self, fuzz_value: str):
        """
        If the fuzz_value is too long, cut it. If it is too short, pad it.

        :type fuzz_value: String
        :param fuzz_value: The fuzz_value to adjust
        :rtype: String
        :return: The adjusted fuzz_value
        """
        if self.max_len is not None and len(fuzz_value) > self.max_len:
            fuzz_value = fuzz_value[: self.max_len]

        if self.min_len is not None and len(fuzz_value) < self.min_len:
            fuzz_value = fuzz_value + self.padding * (self.min_len - len(fuzz_value))

        return fuzz_value

    def mutations(self, default_value):
        """
        On first round, mutate the primitive by stepping through 4 elements, all optionnals.
        The fuzz library, the default value, the long string library, and a file containing a list of strings

        :type default_value: str
        :param default_value: Default value of element.

        :rtype: Generator of strings
        :return: Yield a generator of mutated strings.
        """

        # If round_type is "library", yield library values
        if self.request.parent_session.round_type == "library":
            last_val = None
            for val in itertools.islice(itertools.chain(
                    self._yield_variable_default_value(default_value),
                    self._yield_long_strings(),
                    self._yield_from_file(),
            ), self.num_library_elements):
                # Get the adjusted mutation for the current value if len_unit 'chars'
                if self.len_unit == "chars":
                    current_val = self._adjust_mutation_for_size(val)
                else:
                    current_val = val
                # If the current value is the same as the last value, skip it
                if last_val == current_val:
                    continue
                last_val = current_val
                yield current_val

        # If round_type is "random_mutation", generate random mutations of library values
        elif self.request.parent_session.round_type == "random_mutation":
            # Get all the values from the itertools.chain
            library = list(itertools.chain(
                self._yield_variable_default_value(default_value),
                self._yield_long_strings(),
                self._yield_from_file(),
            ))

            # If the seed index (the round number) is less than or equal to the max_rounds_mutation,
            # mutate the character
            if self.request.parent_session.seed_index < self.max_rounds_mutation:
                # Get the seedth value of the itertools.chain
                # seed isn't only used to generate random, but also as an index
                current_val = self.get_nth(library, self.request.parent_session.seed_index)

                # If the current value is not None, yield the mutated character.
                # If it is None, do nothing.
                random.seed(self.primitive_seed)
                if current_val is not None:
                    for data in self._mutate_character(current_val):
                        if self.len_unit == "chars":
                            yield self._adjust_mutation_for_size(data)
                        else:
                            yield data

        # If round_type is "random_generation", generate random strings
        elif self.request.parent_session.round_type == "random_generation":
            random.seed(self.primitive_seed)
            for _ in range(self.num_random_generations):
                if self.len_unit == "chars":
                    yield self._adjust_mutation_for_size(self.random_generation())
                else:
                    yield self.random_generation()

        # Else, raise an exception
        else:
            raise ValueError("Invalid mutation type")

    def encode(self, value, mutation_context=None):
        value = value.encode(self.encoding, "replace")

        if self.len_unit == "bytes":
            value = self._adjust_mutation_for_size(value)

        return value

    def num_mutations(self, default_value):
        """
        Calculate and return the total number of mutations for this individual primitive.

        Args:
            default_value: Default value of element.

        Returns:
            int: Number of mutated forms this primitive can take
        """
        if self.request.parent_session.round_type == "random_generation":
            return self.num_random_generations

        if self.request.parent_session.round_type == "random_mutation":
            return self.num_random_mutations

        variable_num_mutations = sum(1 for _
                                     in self._yield_variable_default_value(default_value=default_value))
        if self._static_num_mutations is None:
            #  Counting the number of mutations with default value ""
            # results in 0 variable_num_mutations 3 * "" = ""
            self._static_num_mutations = sum(1 for _ in self.mutations(default_value=""))
        return self._static_num_mutations + variable_num_mutations

    def _delete_random_character(self, string_to_mutate: str) -> str:
        """Returns s with a random character deleted"""
        # If string is empty, return it
        if string_to_mutate == "":
            return string_to_mutate

        # Choose a random position in the string
        pos = random.randint(0, len(string_to_mutate) - 1)
        # Remove the character at the chosen position
        return string_to_mutate[:pos] + string_to_mutate[pos + 1:]

    def _insert_random_character(self, string_to_mutate: str) -> str:
        """Returns s with a random character inserted"""
        # Choose a random position in the string
        pos = random.randint(0, len(string_to_mutate))
        # Choose a random character in ASCII printable range
        random_character = chr(random.randrange(32, 127))
        # Insert the random character at the chosen position
        return string_to_mutate[:pos] + random_character + string_to_mutate[pos:]

    def _flip_random_bit(self, string_to_mutate: str):
        """Returns s with a random bit flipped in a random position"""
        if string_to_mutate == "":
            return string_to_mutate

        # Choose a random position in the string
        pos = random.randint(0, len(string_to_mutate) - 1)
        c = string_to_mutate[pos]

        # Choose a random bit to flip
        bit = 1 << random.randint(0, 6)
        new_c = chr(ord(c) ^ bit)

        # Replace the character at the chosen position with the new character
        return string_to_mutate[:pos] + new_c + string_to_mutate[pos + 1:]

    def _mutate_character(self, string_to_mutate: str):
        """
        Takes a raw string and mutates it recursively nbr_mutations times.
        Yields the mutated strings, at each iteration.

        Args:
        string_to_mutate (str): Raw string to mutate.
        nbr_mutations (int): Number of recursive mutations to generate.
        """

        mutators = [
            "_delete_random_character",
            "_insert_random_character",
            "_flip_random_bit"
        ]

        # Mutates recursively nbr_mutations times
        for _ in range(self.num_random_mutations):
            mutator = random.choice(mutators)
            if mutator == "_delete_random_character":
                string_to_mutate = self._delete_random_character(string_to_mutate)
            elif mutator == "_insert_random_character":
                string_to_mutate = self._insert_random_character(string_to_mutate)
            elif mutator == "_flip_random_bit":
                string_to_mutate = self._flip_random_bit(string_to_mutate)
            yield string_to_mutate

    def random_generation(self):
        """
        Generate random strings of size between self.min_len and self.max_len
        return Generated string.
        """
        # Get a random length between min_len and max_len
        length = random.randint(self.min_len, self.max_len)

        # If the encoding is ascii
        if self.encoding == "ascii":
            return ''.join(chr(random.randint(0x00, 0xFF)) for _ in range(length))

        # Generate a string using a range of Unicode characters
        unicode_string = ''.join(
            chr(random.choice([random.randint(0x0000, 0xFFFF), random.randint(0x010000, 0x10FFFF)]))
            for _ in range(length))
        return unicode_string

    # Getters
    def get_default_value_multipliers(self):
        """Getter for _default_value_multipliers"""
        return self._default_value_multipliers

    def get_long_string_lengths(self):
        """Getter for _long_string_lengths"""
        return self._long_string_lengths

    def get_long_string_deltas(self):
        """Getter for _long_string_deltas"""
        return self._long_string_deltas
