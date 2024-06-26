"""
This module contains the Delim primitive.
"""

from .. import helpers
from .string import String


class Delim(String):
    """
    Represent a delimiter such as :,\\r,\\n, ,=,>,< etc... 
    Mutations include repetition, substitution and exclusion.

    :param name: Name, for referencing later. Names should always be provided, but if not,
        a default name will be given, defaults to None
    :type name: str, optional
    :param default_value: Value used when the element is not being fuzzed,
        should typically represent a valid value.
    :type default_value: char, optional
    :param fuzzable: Enable/disable fuzzing of this primitive, defaults to true
    :type fuzzable: bool, optional
    """

    specific_long_string_seeds = [
        " ",
        "\t",
        "\t ",
        "\t\r\n",
        "!",
        "@",
        "#",
        "$",
        "%",
        "^",
        "&",
        "*",
        "(",
        ",",
        "{",
        "}",
        "[",
        "]",
        "-",
        "_",
        "+",
        "=",
        ":",
        ": ",
        ":7",
        ";",
        "'",
        '"',
        "/",
        "\\",
        "?",
        "<",
        ">",
        ".",
        ",",
        "\r",
        "\n",
        "\r\n"
    ]

    def __init__(self, *args, name=None, default_value=" ", **kwargs):
        super().__init__(name=name, default_value=default_value, *args, **kwargs)

        # Add some specific seeds for long strings
        self.long_string_seeds.extend(self.specific_long_string_seeds)
        self.long_string_seeds.append(self._default_value)

    def encode(self, value, mutation_context = None):
        if value is None:
            value = b""
        return helpers.str_to_bytes(value)
