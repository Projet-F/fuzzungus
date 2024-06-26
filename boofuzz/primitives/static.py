from .. import helpers
from .base_primitive import BasePrimitive


class Static(BasePrimitive):
    """Static primitives are fixed and not mutated while fuzzing.

    :type name: str, optional
    :param name: Name, for referencing later. Names should always be provided, but if not, a default name will be given,
        defaults to None
    :type default_value: Raw, optional
    :param default_value: Raw static data
    :type fuzzable: bool, optional
    :param fuzzable: Normaly enable/disable fuzzing of the primitive. 
        Originally wasn't supported by the Static primitive, because it never fuzz. 
        Here, we only catch it to prevent errors when using this parameter instinctively like in the other primitives.
        defaults to False
    """

    def __init__(self, name=None, default_value=None, fuzzable=False, *args, **kwargs):
        super(Static, self).__init__(name=name, default_value=default_value, fuzzable=False, *args, **kwargs)

    def encode(self, value, mutation_context):
        if value is None:
            value = b""
        return helpers.str_to_bytes(value)
