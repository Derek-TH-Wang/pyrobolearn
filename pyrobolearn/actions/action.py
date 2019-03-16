#!/usr/bin/env python
"""Define the Action class.

This file defines the `Action` class, which is returned by the policy and given to the environment.
"""

import numpy as np
import collections
from abc import ABCMeta, abstractmethod
import gym

from pyrobolearn.utils.data_structures.orderedset import OrderedSet


__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "(c) Brian Delhaisse"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class Action(object):
    r"""Action class.

    The `Action` is produced by the policy in response to a certain state/observation. From a programming point of
    view, compared to the `State` class, the action is a setter object. Thus, they have a very close relationship
    and share many functionalities. Some actions are mutually exclusive and cannot be executed at the same time.

    An action is defined as something that affects the environment; that forces the environment to go to the next
    state. For instance, an action could be the desired joint positions, but also an abstract action such as
    'open a door' which would then open a door in the simulator and load the next part of the world.

    In our framework, the `Action` class is decoupled from the policy and environment rendering it more modular [1].
    Nevertheless, the `Action` class still acts as a bridge between the policy and environment. In addition to be
    the output of a policy/controller, it can also be the input to some value estimators, dynamic models, reward
    functions, and so on.

    This class also describes the `action_space` which has initially been defined in `gym.Env` [2].

    References:
        [1] "Wikipedia: Composition over Inheritance", https://en.wikipedia.org/wiki/Composition_over_inheritance
        [2] "OpenAI gym": https://gym.openai.com/   and    https://github.com/openai/gym
    """

    def __init__(self, actions=(), data=None, space=None, name=None):
        """
        Initialize the action. The action contains some kind of data, or is a combination of other actions.

        Args:
            actions (list/tuple of Action): list of actions to be combined together (if given, we can not specified
                                            data)
            data (np.ndarray): data associated to this state
            space (gym.space): space associated with the given data

        Warning:
            Both arguments can not be provided to the action.
        """
        # Check arguments
        if actions is None:
            actions = tuple()

        if not isinstance(actions, (list, tuple, set, OrderedSet)):
            raise TypeError("Expecting a list, tuple, or (ordered) set of actions.")
        if len(actions) > 0 and data is not None:
            raise ValueError("Please specify only one of the argument `actions` xor `data`, but not both.")

        # Check if data is given
        if data is not None:
            if not isinstance(data, np.ndarray):
                if isinstance(data, (list, tuple)):
                    data = np.array(data)
                elif isinstance(data, (int, float)):
                    data = np.array([data])
                else:
                    raise TypeError("Expecting a numpy array, a list/tuple of int/float, or an int/float for 'data'")

        # The following attributes should normally be set in the child classes
        self._data = data
        self._space = space
        self._distribution = None  # for sampling
        self._normalizer = None
        self._noiser = None  # for noise
        self._name = name

        # create ordered set which is useful if this action is a combination of multiple actions
        self._actions = OrderedSet()
        if self._data is None:
            self.add(actions)

        # reset action
        #self.reset()

    ##############################
    # Properties (Getter/Setter) #
    ##############################
    @property
    def actions(self):
        """
        Get the list of actions.
        """
        return self._actions

    @actions.setter
    def actions(self, actions):
        """
        Set the list of actions.
        """
        if self.hasData():
            raise AttributeError("Trying to add internal actions to the current action while it already has some data. "
                                 "A action should be a combination of actions or should contain some kind of data, "
                                 "but not both.")
        if isinstance(actions, collections.Iterable):
            for action in actions:
                if not isinstance(action, Action):
                    raise TypeError("One of the given actions is not an instance of Action.")
                self.add(action)
        else:
            raise TypeError("Expecting an iterator (e.g. list, tuple, OrderedSet, set,...) over actions")

    @property
    def data(self):
        """
        Get the data associated to this particular action, or the combined data associated to each action.

        Returns:
            list of np.ndarray: list of data associated to the action
        """
        if self.hasData():
            return [self._data]
        return [action._data for action in self._actions]

    @data.setter
    def data(self, data):
        """
        Set the data associated to this particular action, or the combined data associated to each action.
        Each data will be clipped if outside the range/bounds of the corresponding action.

        Args:
            data: the data to set
        """
        # one action: change the data
        if self.hasData():
            if not isinstance(data, np.ndarray):
                if isinstance(data, (list, tuple)):
                    data = np.array(data)
                elif isinstance(data, (int, float)):
                    data = data * np.ones(self._data.shape)
                else:
                    raise TypeError("Expecting a numpy array, a list/tuple of int/float, or an int/float for 'data'")

            if self._data.shape != data.shape:
                raise ValueError("The given data does not have the same shape as previously.")

            # clip the value using the space
            if self.hasSpace():
                if self.isContinuous():  # continuous case
                    low, high = self._space.low, self._space.high
                    data = np.clip(data, low, high)
                else: # discrete case
                    n = self._space.n
                    if data.size == 1:
                        data = np.clip(data, 0, n)
            self._data = data

        else:  # combined action
            if not isinstance(data, collections.Iterable):
                raise TypeError("data is not an iterator")
            if len(self._actions) != len(data):
                raise ValueError("The number of actions is different from the number of data segments")
            for action, d in zip(self._actions, data):
                action.data = d

    @property
    def space(self):
        """
        Get the corresponding space.
        """
        if self.hasSpace():
            return [self._space]
        return [action._space for action in self._actions]

    @space.setter
    def space(self, space):
        """
        Set the corresponding space. This can only be used one time!
        """
        if self.hasData() and not self.hasSpace() and \
                isinstance(space, (gym.spaces.Box, gym.spaces.Discrete)):
            self._space = space

    @property
    def name(self):
        """
        Return the name of the action.
        """
        if self._name is None:
            return self.__class__.__name__
        return self._name

    @name.setter
    def name(self, name):
        """
        Set the name of the action.
        """
        if not isinstance(name, str):
            raise TypeError("Expecting the name to be a string.")
        self._name = name

    @property
    def shape(self):
        """
        Return the shape of each action. Some actions, such as camera actions have more than 1 dimension.
        """
        # if self.hasActions():
        return [d.shape for d in self.data]
        # return [self.data.shape]

    @property
    def size(self):
        """
        Return the size of each action.
        """
        # if self.hasActions():
        return [d.size for d in self.data]
        # return [len(self.data)]

    @property
    def dimension(self):
        """
        Return the dimension (length of shape) of each action.
        """
        return [len(d.shape) for d in self.data]

    @property
    def distribution(self):
        """
        Get the current distribution used when sampling the action
        """
        pass

    @distribution.setter
    def distribution(self, distribution):
        """
        Set the distribution to the action.
        """
        # check if distribution is discrete/continuous
        pass

    ###########
    # Methods #
    ###########
    def isCombinedAction(self):
        """
        Return a boolean value depending if the action is a combination of actions.

        Returns:
            bool: True if the action is a combination of actions, False otherwise.
        """
        return len(self._actions) > 0

    # alias
    hasActions = isCombinedAction

    def hasData(self):
        return self._data is not None

    def hasSpace(self):
        return self._space is not None

    def add(self, action):
        """
        Add a action or a list of actions to the list of internal actions. Useful when combining different actions
        together. This shouldn't be called if this action has some data set to it.

        Args:
            action (Action, list/tuple of Action): action(s) to add to the internal list of actions
        """
        if self.hasData():
            raise AttributeError("Undefined behavior: a action should be a combination of actions or should contain "
                                 "some kind of data, but not both.")
        if isinstance(action, Action):
            self._actions.add(action)
        elif isinstance(action, collections.Iterable):
            for i, s in enumerate(action):
                if not isinstance(s, Action):
                    raise TypeError("The item {} in the given list is not an instance of Action".format(i))
                self._actions.add(s)
        else:
            raise TypeError("The 'other' argument should be an instance of Action, or an iterator over actions.")

    # alias
    append = add
    extend = add

    def _write(self, data=None):
        pass

    def write(self, data=None):
        """
        Write the action values to the simulator for each action.
        This has to be overwritten by the child class.
        """
        if self.hasData():  # write the current action
            self._write(data)
        else:  # read each action
            if self.actions:
                for action, d in zip(self.actions, data):
                    action._write(d)

        # return the data
        # return self.data

    # def _reset(self):
    #     pass
    #
    # def reset(self):
    #     """
    #     Some actions need to be reset. It returns the initial action.
    #     This needs to be overwritten by the child class.
    #
    #     Returns:
    #         initial action
    #     """
    #     if self.hasData(): # reset the current action
    #         self._reset()
    #     else: # reset each action
    #         for action in self.actions:
    #             action._reset()
    #
    #     # return the first action data
    #     return self.write()

    # def shape(self):
    #     """
    #     Return the shape of each action. Some actions, such as camera actions have more than 1 dimension.
    #     """
    #     return [d.shape for d in self.data]
    #
    # def dimension(self):
    #     """
    #     Return the dimension (length of shape) of each action.
    #     """
    #     return [len(d.shape) for d in self.data]

    def maxDimension(self):
        """
        Return the maximum dimension.
        """
        return max(self.dimension)

    # def size(self):
    #     """
    #     Return the size of each action.
    #     """
    #     return [d.size for d in self.data]

    def totalSize(self):
        """
        Return the total size of the combined action.
        """
        return sum(self.size)

    def hasDiscreteValues(self):
        """
        Does the action have discrete values?
        """
        if self._data is None:
            return [isinstance(action._space, gym.spaces.Discrete) for action in self._actions]
        if isinstance(self._space, gym.spaces.Discrete):
            return [True]
        return [False]

    def isDiscrete(self):
        """
        If all the actions are discrete, then it is discrete.
        """
        return all(self.hasDiscreteValues())

    def hasContinuousValues(self):
        """
        Does the action have continuous values?
        """
        if self._data is None:
            return [isinstance(action._space, gym.spaces.Box) for action in self._actions]
        if isinstance(self._space, gym.spaces.Box):
            return [True]
        return [False]

    def isContinuous(self):
        """
        If one of the action is continuous, then the action is considered to be continuous.
        """
        return any(self.hasContinuousValues())

    def bounds(self):
        """
        If the action is continuous, it returns the lower and higher bounds of the action.
        If the action is discrete, it returns the maximum number of discrete values that the action can take.

        Returns:
            list/tuple: list of bounds if multiple actions, or bounds of this action
        """
        if self._data is None:
            return [action.bounds() for action in self._actions]
        if isinstance(self._space, gym.spaces.Box):
            return (self._space.low, self._space.high)
        elif isinstance(self._space, gym.spaces.Discrete):
            return (self._space.n,)
        raise NotImplementedError

    def apply(self, fct):
        """
        Apply the given fct to the data of the action, and set it to the action.
        """
        self.data = fct(self.data)

    def contains(self, x):  # parameter dependent of the action
        """
        Check if the argument is within the range/bound of the action.
        """
        return self._space.contains(x)

    def sample(self, distribution=None):  # parameter dependent of the action (discrete and continuous distributions)
        """
        Sample some values from the action based on the given distribution.
        If no distribution is specified, it samples from a uniform distribution (default value).
        """
        if self.isCombinedAction():
            return [action.sample() for action in self._actions]
        if self._distribution is None:
            return
        else:
            pass
        raise NotImplementedError

    def addNoise(self, noise=None, replace=True):  # parameter dependent of the action
        """
        Add some noise to the action, and returns it.

        Args:
            noise (np.ndarray, fct): array to be added or function to be applied on the data
        """
        if self._data is None:
            # apply noise
            for action in self._actions:
                action.addNoise(noise=noise)
        else:
            # add noise to the data
            noisy_data = self.data + noise
            # clip such that the data is within the bounds
            self.data = noisy_data

    def normalize(self, normalizer=None, replace=True):  # parameter dependent of the action
        """
        Normalize using the action data using the provided normalizer.

        Args:
            normalizer (sklearn.preprocessing.Normalizer): the normalizer to apply to the data.
            replace (bool): if True, it will replace the `data` attribute by the normalized data.

        Returns:
            the normalized data
        """
        pass

    ########################
    # Operator Overloading #
    ########################

    def __repr__(self):
        if self._data is None:
            lst = [self.__class__.__name__ + '(']
            for action in self.actions:
                lst.append('\t' + action.__repr__() + ',')
            lst.append(')')
            return '\n'.join(lst)
        else:
            return '%s(%s)' % (self.name, self._data)

    # def __str__(self):
    #     """
    #     String to represent the action. Need to be provided by each child class.
    #     """
    #     if self._data is None:
    #         return [str(action) for action in self._actions]
    #     return str(self)

    def __call__(self, data=None):
        """
        Compute/read the action and return it. It is an alias to the `self.write()` method.
        """
        return self.write(data)

    def __len__(self):
        """
        Return the total number of actions contained in this class.

        Example::

            s1 = JntPositionAction(robot)
            s2 = s1 + JntVelocityAction(robot)
            print(len(s1)) # returns 1
            print(len(s2)) # returns 2
        """
        if self._data is None:
            return len(self._actions)
        return 1

    def __iter__(self):
        """
        Iterator over the actions.
        """
        if self.isCombinedAction():
            for action in self._actions:
                yield action
        else:
            yield self

    def __contains__(self, item):
        """
        Check if the action item(s) is(are) in the combined action. If the item is the data associated with the action,
        it checks that it is within the bounds.

        Args:
            item (Action, list/tuple of action): check if given action(s) is(are) in the combined action

        Example:
            s1 = JntPositionAction(robot)
            s2 = JntVelocityAction(robot)
            s = s1 + s2
            print(s1 in s) # output True
            print(s2 in s1) # output False
            print((s1, s2) in s) # output True
        """
        # check type of item
        if not isinstance(item, (Action, np.ndarray)):
            raise TypeError("Expecting a action or numpy array.")

        # check if action item is in the combined action
        if self._data is None and isinstance(item, Action):
            return (item in self._actions)

        # check if action/data is within the bounds
        if isinstance(item, Action):
            item = item.data

        # check if continuous
        # if self.isContinuous():
        #     low, high = self.bounds()
        #     return np.all(low <= item) and np.all(item <= high)
        # else: # discrete case
        #     num = self.bounds()[0]
        #     # check the size of data
        #     if item.size > 1: # array
        #         return (item.size < num)
        #     else: # one number
        #         return (item[0] < num)

        return self.contains(item)

    def __getitem__(self, key):
        """
        Get the corresponding item from the action(s)
        """
        # if one action, slice the corresponding action data
        if len(self._actions) == 0:
            return self._data[key]
        # if multiple actions
        if isinstance(key, int):
            # get one action
            return self._actions[key]
        elif isinstance(key, slice):
            # get multiple actions
            return Action(self._actions[key])
        else:
            raise TypeError("Expecting an int or slice for the key, but got instead {}".format(type(key)))

    def __setitem__(self, key, value):
        """
        Set the corresponding item/value to the corresponding key.

        Args:
            key (int, slice): index of the internal action, or index/indices for the action data
            value (Action, int/float, array): value to be set
        """
        if self.isCombinedAction():
            # set/move the action to the specified key
            if isinstance(value, Action) and isinstance(key, int):
                self._actions[key] = value
            else:
                raise TypeError("Expecting key to be an int, and value to be a action.")
        else:
            # set the value on the data directly
            self._data[key] = value

    def __add__(self, other):
        """
        Combine two different actions together. In this special case, the operation is not commutable.
        This is the same as taking the union of the actions.

        Args:
            other (Action): another action

        Returns:
            Action: the combined action

        Examples:
            s1 = JntPositionAction(robot)
            s2 = JntVelocityAction(robot)
            s = s1 + s2     # = Action([JntPositionAction(robot), JntVelocityAction(robot)])

            s1 = Action([JntPositionAction(robot), JntVelocityAction(robot)])
            s2 = Action([JntPositionAction(robot), LinkPositionAction(robot)])
            s = s1 + s2     # = Action([JntPositionAction(robot), JntVelocityAction(robot), LinkPositionAction(robot)])
        """
        if not isinstance(other, Action):
            raise TypeError("Expecting another action, instead got {}".format(type(other)))
        s1 = self._actions if self._data is None else OrderedSet([self])
        s2 = other._actions if other._data is None else OrderedSet([other])
        s = s1 + s2
        return Action(s)

    def __iadd__(self, other):
        """
        Add a action to the current one.

        Args:
            other (Action, list/tuple of Action): other action

        Examples:
            s = Action()
            s += JntPositionAction(robot)
            s += JntVelocityAction(robot)
        """
        if self._data is not None:
            raise AttributeError("The current class already has some data attached to it. This operation can not be "
                                 "applied in this case.")
        self.append(other)

    def __sub__(self, other):
        """
        Remove the other action(s) from the current action.
        :param other:
        :return:
        """
        if not isinstance(other, Action):
            raise TypeError("Expecting another action, instead got {}".format(type(other)))
        s1 = self._actions if self._data is None else OrderedSet([self])
        s2 = other._actions if other._data is None else OrderedSet([other])
        s = s1 - s2
        if len(s) == 1: # just one element
            return s[0]
        return Action(s)

    def __isub__(self, other):
        """
        Remove one or several actions from the combined action.

        Args:
            other:
        """
        if not isinstance(other, Action):
            raise TypeError("Expecting another action, instead got {}".format(type(other)))
        if self._data is not None:
            raise RuntimeError("This operation is only available for a combined action")
        s = other._actions if other._data is None else OrderedSet([other])
        self._actions -= s
