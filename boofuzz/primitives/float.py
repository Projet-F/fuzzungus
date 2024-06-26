import random
import struct
import sys

from .base_primitive import BasePrimitive


class Float(BasePrimitive):
    """Primitive that generates random float values within a specific range and with a fixed format.

    :type name: str, optional
    :param name: Name, for referencing later.
    :type default_value: float
    :param default_value: Value used when the element is not being fuzzed.
    :type s_format: str, optional
    :param s_format: Format of the float value on encoding, like .1f, defaults to None 
    :type f_min: float, optional
    :param f_min: Minimal float value that can be generated while fuzzing, defaults to sys.float_info.min
    :type f_max: float, optional
    :param f_max: Maximal float value that can be generated while fuzzing, defaults to sys.float_info.max
    :type max_mutations: int, optional
    :param max_mutations: Total number of mutations for this individual primitive, defaults to 1000
    :type encode_as_ieee_754: bool, optional
    :param encode_as_ieee_754: Encode the float value as IEEE 754 floating point
    :type endian: str, optional
    :param endian: Change the endianness of IEEE 754 float point representation, defaults to big endian
    """

    _fuzz_library = [
        sys.float_info.epsilon,
        sys.float_info.min,
        sys.float_info.max,
        sys.float_info.min_exp,
        sys.float_info.min_10_exp,
        sys.float_info.max_exp,
        sys.float_info.max_10_exp,
        float("inf"),
        float("-inf"),
    ]

    def __init__(
        self,
        *args,
        name=None,
        default_value=0.0,
        s_format=None,
        f_min=sys.float_info.min,
        f_max=sys.float_info.max,
        max_mutations=1000,
        encode_as_ieee_754=False,
        endian="big",
        **kwargs
    ):
        super().__init__(name=name, default_value=str(default_value), *args, **kwargs)

        self.s_format = s_format
        self.f_min = f_min
        self.f_max = f_max
        self.max_mutations = max_mutations
        self.encode_as_ieee_754 = encode_as_ieee_754
        self.endian = endian
        if self.s_format:
            self.str_format = "%" + self.s_format

    def mutations(self, default_value):
        # If the mutation type is library, yield the default value and the library values
        if self.request.parent_session.mutation_type == "library" :
            # Yield the default value first
            yield default_value
            last_val = default_value

            # Yield the library values, checking for duplicates
            for val in self._fuzz_library:
                if last_val == val:
                    continue
                last_val = val
                yield self.format_value(val)

        # If the mutation type is random_mutation or random_generation, yield random float values
        elif self.request.parent_session.mutation_type in ("random_mutation", "random_generation") :
            random.seed(self.request.primitive_seed)
            for _ in range(self.num_random_generations):
                yield self.format_value(self.random_generation())

        # Otherwise, raise an error
        else :
            raise ValueError("Invalid mutation type")


    def random_generation(self):
        # Generate a random float value
        random_val = random.choice([
            random.uniform(self.f_min, self.f_max), # Random float value
            format(random.uniform(0,1), f'.{sys.float_info.mant_dig}f') # Random float value with maximum precision
            ])

        return random_val

    def format_value(self, value):
        """
        param value: float, value to be formatted
        return: str
        """
        # If the format is set, format the value
        if self.s_format:
            return self.str_format % float(value)
        # Otherwise, return the value as a string
        return str(value)

    def encode(self, value, mutation_context=None):
        if self.encode_as_ieee_754:
            value = float(value)
            return self.__convert_to_iee_754(value)

        return value.encode()

    def __convert_to_iee_754(self, value):
        if self.endian == "big":
            iee_value = struct.pack(">f", value)
        elif self.endian == "little":
            iee_value = struct.pack("<f", value)
        else:
            error_msg = f"Invalid endian argument '{self.endian}'. Use 'big' or 'little'."
            raise ValueError(error_msg)

        return iee_value

    def num_mutations(self, default_value):
        return self.max_mutations
