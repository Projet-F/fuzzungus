"""Module for the base primitive class"""
import os, itertools
from ..fuzzable import Fuzzable


class BasePrimitive(Fuzzable):
    """
    The primitive base class implements common functionality shared across most primitives.

    ..versionchanged:: 1.0.0
        All the parameters below and associated methods where move from the Fuzzable class to
        the BasePrimitive class, as some classes that are not primitives inherints from Fuzzable,
        and they don't need these parameters.

    :type min_len: int, optional
    :param min_len: Minimum length of the generated values, defaults to 0
    :type max_len: int, optional
    :param max_len: Maximum length of the generated values, defaults to 1000
    :type num_library_elements: int, optional
    :param num_library_elements: Number of elements in the library, defaults to 50
    :type num_random_generations: int, optional
    :param num_random_generations: Number of random elements to generate, defaults to 50
    :type num_random_mutations: int, optional
    :param num_random_mutations: Number of random mutations to generate on one element
        of the initial library, defaults to 40
    :type max_rounds_mutation: int, optional
    :param max_rounds_mutation: Maximum number of rounds of mutation, defaults to 1500. 
        If the size of the library from which the mutations are done is greater than this value, 
        the mutation is only done on the first max_rounds_mutation elements.
    :type seclist_path: str, optional
    :param seclist_path: Path to the seclist file, defaults to ""
    """

    def __init__(self,
                min_len=0, max_len=1000,
                seclist_path="",
                num_random_generations=50, num_random_mutations=40, num_library_elements=50,
                max_rounds_mutation=1500,
                *args, **kwargs):
        super(BasePrimitive, self).__init__(*args, **kwargs)
        self._fuzz_library = []  # library of static fuzz heuristics to cycle through.

        # Number of elements to yield per round type
        self.num_random_generations = num_random_generations
        self.num_random_mutations = num_random_mutations
        self.num_library_elements = num_library_elements
        self.max_rounds_mutation = max_rounds_mutation

        # Length parameters
        self.min_len = min_len
        self.max_len = max_len

        # Check if seclist file exists, otherwise raise an exception
        # This check is done in __init__ to raise the exception before
        #   the beggining of the fuzzing campaign
        self.seclist_path = seclist_path
        self._get_seclist_abs_path()

    def mutations(self, default_value):
        for val in self._fuzz_library:
            yield val

    def encode(self, value, mutation_context):
        if value is None:
            value = b""
        return value

    def num_mutations(self, default_value):
        return len(self._fuzz_library)
    
    def get_nth(self, iterator, n):
        """Return the nth item or None"""
        # If the nth element is bigger than the max number of mutations, return None
        if n > self.max_rounds_mutation:
            return None
        # return the nth item or None if it doesn't exist
        return next(itertools.islice(iterator, n, None), None)

    def _get_seclist_abs_path(self):
        """Return the absolute path of the seclist file"""
        inside_docker = os.getenv('INSIDE_DOCKER', False)

        if inside_docker:
            abs_seclist_path = os.path.join('/app/data/', self.seclist_path)
        else:
            # Get this file path
            file_path = os.path.abspath(__file__)
            # Strip the file name and the two last directories from the path
            dir_path = os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
            # Add /data to the path
            data_dir_path = os.path.join(dir_path, "data")
            # Get seclist file path
            abs_seclist_path = os.path.join(data_dir_path, self.seclist_path)

        # Check if the seclist file exists, otherwise raise an exception
        if self.seclist_path != "" and not os.path.isfile(abs_seclist_path):
            raise FileNotFoundError(f"File not found: {abs_seclist_path}")

        # Return the absolute path of the seclist file
        return abs_seclist_path