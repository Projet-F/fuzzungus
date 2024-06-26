from __future__ import annotations

import collections
from boofuzz.primitives import *

from .. import exception
from ..constants import ERR_NAME_NO_RESOLVE, ERR_NAME_NOT_FOUND, ERR_NAME_TOO_MANY
from ..exception import BoofuzzNameResolutionError
from ..fuzzable import Fuzzable
from ..fuzzable_block import FuzzableBlock
from ..pgraph.node import Node

import typing

if typing.TYPE_CHECKING:
    from boofuzz.sessions import Session


class Request(FuzzableBlock, Node):
    """Top level container. Can hold any block structure or primitive.

    This can essentially be thought of as a super-block, root-block, daddy-block or whatever other alias you prefer.

    Here are the parameters of the Request class:

    :type name: str, optional
    :param name: Name of this request
    :type children: boofuzz.Fuzzable, optional
    :param children: Children of this request, defaults to None
    :type timeout_check: bool, optional
    :param timeout_check: If True, check for timeout, defaults to True
    :type fragmentation: typing.Callable, optional
    :param fragmentation: Fragmentation function, defaults to None
    :type fragmentation_length: int, optional
    :param fragmentation_length: Fragmentation length, defaults to 516
    :type receive_data_after_transmit: bool, optional
    :param receive_data_after_transmit: default to True, force the request to not wait answer if False
    :type answer_must_contain: list[str|bytes], optional
    :param answer_must_contain: List of strings or bytes that the answer must contain, defaults to None
    :type answer_must_not_contain: list[str|bytes], optional
    :param answer_must_not_contain: List of strings or bytes that the answer must not contain, defaults to None

    And it's attributes:

    :type parent_session: boofuzz.Session
    :param parent_session: Parent session of this Request, so children can now access parameters of session.
    :type smooth_rtt: float
    :param smooth_rtt: Smoothed Round Trip Time
    :type rtt_variations: float
    :param rtt_variations: Round Trip Time Variations
    """

    def __init__(self, name=None, children: tuple[BasePrimitive, ...] = None, timeout_check: bool = True,
                 fragmentation: typing.Callable = None,
                 fragmentation_length: int = 516,
                 receive_data_after_transmit:bool=True,
                 answer_must_contain: list[str|bytes]|None = None, answer_must_not_contain: list[str|bytes]|None = None):
        FuzzableBlock.__init__(self, name=name, request=self)
        Node.__init__(self)
        self.label = name  # node label for graph rendering.
        self.stack = []  # the request stack.
        self.block_stack = []  # list of open blocks, -1 is last open block.
        self.callbacks = collections.defaultdict(list)
        self.names = {name: self}  # dictionary of directly accessible primitives.
        self._rendered = b""  # rendered block structure.
        self._mutant_index = 0  # current mutation index.
        self._element_mutant_index = None  # index of current mutant element within self.stack
        self.mutant: Fuzzable | None = None  # current primitive being mutated.
        self.parent_session: Session | None = None  # Parent session of this Request, so children can now access parameters of session.
        self.requests: list[Request] = None

        # Timeout parameters and attributes
        self.timeout_check: bool = timeout_check  # If True, check for timeout
        self.smooth_rtt: float = 0  # Smoothed Round Trip Time
        self.rtt_variations: float = 0  # Round Trip Time Variations
        self.rto: float = 100  # Retransmission Timeout

        self.receive_data_after_transmit:bool = receive_data_after_transmit
        self.answer_must_contain: list[str|bytes] | None = answer_must_contain
        self.answer_must_not_contain: list[str|bytes] | None = answer_must_not_contain

        # Fragmentation parameters
        self.fragmentation = fragmentation
        self.fragmentation_length: int = fragmentation_length

        # If the children is None, then we initialize an empty list
        if children is None:
            children = []
        # If the children is a Fuzzable, then we put it in a list
        elif isinstance(children, Fuzzable):
            children = [children]
        # Initialize the children of the request
        self._check_multiple_default_fields(child_nodes=children)

    def _check_multiple_default_fields(self, child_nodes: tuple[BasePrimitive, ...], block_stack=None):
        """
        Search in the children of the request if there is a MultipleDefault field.
        If there is one, then we initialize the requests with the right values.

        @type child_nodes: tuple[BasePrimitive, ...]
        @param child_nodes: Children of the request
        @type block_stack: list
        @param block_stack: List of open blocks, -1 is last open block
        """

        self.requests = []
        if block_stack is None:
            block_stack = list()

        # Search if there is a multipledefaultfield, if there is one, then count how many values there are.
        multipledefaultfield = False
        for item in child_nodes:
            if isinstance(item, MultipleDefault):
                multipledefaultfield = True
                self._initialize_multiple_requests(child_nodes, block_stack, item=item)

        if not multipledefaultfield:
            self.requests.append(self)
            # If there is not multipledefaultfield, then only initialize 1 request
            self._initialize_children(child_nodes, block_stack=block_stack)

    def _initialize_children(self, child_nodes, block_stack=None):
        """
        Initialize the children of the request.
        """

        for item in child_nodes:
            item.context_path = self._generate_context_path(block_stack)
            item.request = self
            # ensure the name doesn't already exist.
            if item.qualified_name in list(self.names):
                raise exception.SullyRuntimeError(f"BLOCK NAME ALREADY EXISTS: {item.qualified_name}")
            self.names[item.qualified_name] = item

            if len(block_stack) == 0:
                self.stack.append(item)
            if isinstance(item, FuzzableBlock):
                block_stack.append(item)
                self._initialize_children(child_nodes=item.stack, block_stack=block_stack)
                block_stack.pop()

    def _initialize_multiple_requests(self, child_nodes, block_stack=None, item=None):
        # First time we enter this function, we have to initialize the first request
        if len(self.requests) == 0:
            self.requests.append(self)
            self._initialize_children(child_nodes, block_stack=block_stack)

        # Here, we add as many requests as we need to test every case
        # Exemple : [0,1] and [2,3] --> [[0,2],[0,3],[0],[1,2],[1,3],[1]]
        for i in range(0, len(self.requests) * len(item.values) + len(self.requests), len(item.values) + 1):
            for j in range(0, len(item.values)):
                newrequest = Request(name=self.requests[i].label + "_" + str(j))
                newrequest.stack = self.requests[i].stack.copy()
                self.requests.insert(i + j + 1, newrequest)
        j = 0
        # We remove useless requests [[0,2],[0,3],[0],[1,2],[1,3],[1]] --> [[0,2],[0,3],[1,2],[1,3]]
        for i in range(0, len(self.requests), len(item.values) + 1):
            self.requests.pop(i - j)
            j += 1
        # For each request, we replace the first MultipleDefault field by the right field.
        # Others MultipleDefault fields are replaced in the next call of this function
        index = 0
        for request in self.requests:
            i = 0
            for item in request.stack:
                if isinstance(item, MultipleDefault):
                    if index == 0:
                        default = item.values[index % len(item.values)]
                        request.stack[i] = item.primitive(name=item.name + str(i), default_value=default, **item.kwargs)
                        request.stack[i].request = self
                    else:
                        #For other requests, change the multipledefaultfield with a Static type
                        request.stack[i] = Static(name=item.name, default_value = item.values[index % len(item.values)])
                    # break of the loop because the precedent for loops create more Requests to have one MultipleDefault
                    # field by Request
                    break
                i += 1
            index += 1

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def fuzzable(self):
        return True

    def pop(self):
        """
        The last open block was closed, so pop it off of the block stack.
        """

        if not self.block_stack:
            raise exception.SullyRuntimeError("BLOCK STACK OUT OF SYNC")

        self.block_stack.pop()

    def push(self, item):
        """
        Push an item into the block structure. If no block is open, the item goes onto the request stack. otherwise,
        the item goes onto the last open blocks stack.

        What this method does:
        1. Sets context_path for each pushed FuzzableWrapper.
        2. Sets request for each FuzzableWrapper
        3. Checks for duplicate qualified_name items
        4. Adds item to self.names map (based on qualified_name)
        5. Adds the item to self.stack, or to the stack of the currently opened block.

        Also: Manages block_stack, mostly an implementation detail to help static protocol definition

        @type item: BasePrimitive | Block | Request | Size | Repeat
        @param item: Some primitive/block/request/etc.
        """
        item.context_path = self._generate_context_path(self.block_stack)
        item.request = self
        # ensure the name doesn't already exist.
        if item.qualified_name in list(self.names):
            raise exception.SullyRuntimeError("BLOCK NAME ALREADY EXISTS: %s" % item.qualified_name)

        self.names[item.qualified_name] = item

        # if there are no open blocks, the item gets pushed onto the request stack.
        # otherwise, the pushed item goes onto the stack of the last opened block.
        if not self.block_stack:
            self.stack.append(item)
        else:
            self.block_stack[-1].push(item)

        # add the opened block to the block stack.
        if isinstance(item, FuzzableBlock):
            self.block_stack.append(item)

    def _generate_context_path(self, block_stack):
        context_path = ".".join(x.name for x in block_stack)  # TODO put in method
        context_path = ".".join(filter(None, (self.name, context_path)))
        return context_path

    def render(self, mutation_context=None):
        if self.block_stack:
            raise exception.SullyRuntimeError("UNCLOSED BLOCK: %s" % self.block_stack[-1].qualified_name)

        return self.get_child_data(mutation_context=mutation_context)

    def walk(self, stack=None):
        """
        Recursively walk through and yield every primitive and block on the request stack.

        @param stack: Set to none -- used internally by recursive calls.
                      If None, uses self.stack.

        @rtype:  Sulley Primitives
        @return: Sulley Primitives
        """

        if not stack:
            stack = self.stack

        for item in stack:
            # if the item is a block, step into it and continue looping.
            if isinstance(item, FuzzableBlock):
                for stack_item in self.walk(item.stack):
                    yield stack_item
            else:
                yield item

    def resolve_name(self, context_path, name):
        """
        Names are resolved thus:
        #. If the name starts with a dot, it is treated as a relative path name in the style of PEP 328.

           #. "." refers to the current directory, so to speak.
           #. ".." refers to the next directory up.
           #. "..." refers to another directory up, and so forth.

        #. If the name does _not_ start with a dot, it is treated as an absolute name.
        #. Backwards compatibility: If the absolute name fails to resolve, the engine searches for any block or
            primitive with that name. If more or less than exactly one match is found, an error results.

        Args:
            context_path: The "current working directory" for resolving the name. E.g. "block_1.block_2".
            name: The name being resolved. May be absolute or relative.

        Returns:

        """
        if name is None:
            raise BoofuzzNameResolutionError(ERR_NAME_NOT_FOUND.format(name))
        if name.startswith("."):  # Case 1 relative
            components = (context_path + name).split(".")  # double dots leave an empty string; so do trailing dots
            while "" in components:
                i = components.index("")
                if i <= 0:
                    raise BoofuzzNameResolutionError(ERR_NAME_NO_RESOLVE.format(name, context_path))
                elif i == len(components) - 1:  # last in list; indicates a trailing dot
                    del components[i]
                else:  # double dot
                    del components[i]
                    del components[i - 1]
            return self._lookup_resolved_name(".".join(components))
        else:
            full_absolute_name = "{0}.{1}".format(self._name, name)
            if full_absolute_name in self.names:  # Case 2 absolute
                return self._lookup_resolved_name(full_absolute_name)
            else:  # Case 3 backwards compatibility --  look up by last name component
                found_names = [n for n in self.names if n.rsplit(".")[-1] == name]
                if len(found_names) == 1:
                    return self.names[found_names[0]]
                elif len(found_names) == 0:
                    raise BoofuzzNameResolutionError(ERR_NAME_NOT_FOUND.format(name))
                else:
                    raise BoofuzzNameResolutionError(ERR_NAME_TOO_MANY.format(name, found_names))

    def _lookup_resolved_name(self, resolved_name):
        if resolved_name in self.names:
            return self.names[resolved_name]
        else:
            raise BoofuzzNameResolutionError(ERR_NAME_NOT_FOUND.format(resolved_name))

    def get_mutations(self, default_value=None, skip_elements=None):
        return self.mutations(default_value=default_value, skip_elements=skip_elements)

    def get_num_mutations(self):
        return self.num_mutations()

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def calculate_rto(self, rtt:float, alpha:float=0.125, beta:float=0.25, k:int=4) -> float:
        """
        Public method to calculate a new retransmission timeout using TCP formula :

        .. math::

            srtt = (1 - g).srtt + g.rtt

            rttvar = (1 - h).rttvar + h.|rtt - srtt|

            RTO = srtt + 4.rttvar

        See `RFC 6298 <https://www.rfc-editor.org/rfc/rfc6298>`_ for more information.

        :param rtt: The new round trip time
        :type rtt: float
        :param alpha: The alpha value of the formula.
            This gain factor determines how quickly the smoothed round-trip time (srtt) responds to changes in the measured round-trip time.
            A larger alpha makes srtt more sensitive to recent changes, making it adapt faster to network conditions.
            A smaller alpha makes srtt more stable but slower to react to changes.
            Optional, defaults to 0.125
        :type alpha: float
        :param beta: The beta value of the formula.
            This gain factor affects how the round-trip time variation (rttvar) responds to changes in the deviation of the measured round-trip time from srtt.
            A larger beta makes rttvar more sensitive to fluctuations, capturing changes in variability more quickly.
            A smaller beta makes rttvar more stable but slower to adapt to new conditions.
            Optional, defaults to 0.25
        :type beta: float
        :param k: The k value of the formula.
            A larger value provides more buffer.
            Changes not recommended.
        :type k: int

        :return: The new retransmission timeout
        """

        # If it is the first rtt measurement, we set the initial values
        if self.rto == 100:
            self.smooth_rtt = rtt
            self.rtt_variations = rtt / 2
            self.rto = self.smooth_rtt + k * self.rtt_variations
        else:
            # calculate the new round trip time variations
            self.rtt_variations = (1 - beta) * self.rtt_variations + beta * abs(rtt - self.smooth_rtt)

            # calculate the new smooth round trip time
            self.smooth_rtt = (1 - alpha) * self.smooth_rtt + alpha * rtt

            # calculate the new retransmission timeout
            self.rto = self.smooth_rtt + 4 * self.rtt_variations

        return self.rto

    def analyze_answer(self, data:bytes, session:Session) -> None :
        """
        If answer_must_contains or answer_must_not_contains is filled, when we got an anwer,
        we analyze it and log it

        :return: None
        """

        if self.answer_must_contain:
            for expected in self.answer_must_contain:
                if isinstance(expected, str):
                    expected = expected.encode('utf-8')
                if expected in data:
                    session.get_fuzz_data_logger().log_info("Expected answer")
                    return
        if self.answer_must_not_contain:
            for forbidden in self.answer_must_not_contain:
                if isinstance(forbidden, str):
                    forbidden = forbidden.encode('utf-8')
                if forbidden in data:
                    session.get_fuzz_data_logger().log_target_error("Forbidden answer")
                    return
        session.get_fuzz_data_logger().log_target_warn("Unexpected answer")
        return
