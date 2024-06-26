from .base_primitive import BasePrimitive


class MultipleDefault(BasePrimitive):
    """This primitive represents a list of static values, stepping through each one on mutation.

    You can tie a block
    to a group primitive to specify that the block should cycle through all possible mutations for *each* value
    within the group. The group primitive is useful for example for representing a list of valid opcodes.

    :param name: Name, for referencing later. Names should always be provided, but if not, a default name will be given,
        defaults to None
    :type name: str, optional
    :param values: List of possible raw values this group can take.
    :type values: list of bytes or list of str
    :param default_value: Value used when the element is not being fuzzed - should typically represent a valid value,
        defaults to None
    :type default_value: str, optional
    :param encoding: String encoding, ex: utf_16_le for Microsoft Unicode, defaults to ascii
    :type encoding: str, optional
    :param fuzzable: Enable/disable fuzzing of this primitive, defaults to true
    :type fuzzable: bool, optional
    """

    def __init__(self, name=None, values=None, default_value=None,primitive:BasePrimitive=BasePrimitive, *args, **kwargs):
        assert len(values) > 0, "You can't have an empty value list for your group!"
        for val in values:
            assert isinstance(val, (bytes, str)), "Value list may only contain string/byte types"

        if default_value is None:
            default_value = values[0]

        self.primitive=primitive

        self.kwargs = kwargs

        super(MultipleDefault, self).__init__(name=name, default_value=default_value, *args, **kwargs)

        self.values = values