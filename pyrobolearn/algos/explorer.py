#!/usr/bin/env python
"""Provide the Explorer class used in the first step of RL algorithms

It consists to explore and collect samples in the environment using the policy. The samples are stored in the
given memory/storage unit which will be used to evaluate the policy, and then update its parameters.
"""

import inspect

from pyrobolearn.tasks import RLTask
from pyrobolearn.envs import Env
from pyrobolearn.policies import Policy
from pyrobolearn.exploration import Exploration
from pyrobolearn.storages import DictStorage  # RolloutStorage

from pyrobolearn import logger

__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class Explorer(object):
    r"""Explorer

    (Model-free) reinforcement learning algorithms requires 3 steps:
    1. Explore: Explore and collect samples in the environment using the policy. The samples are stored in the
                given memory/storage unit.
    2. Evaluate: Assess the quality of the actions/trajectories using the returns.
    3. Update: Update the policy (and/or value function) parameters based on the loss

    This class focuses on the first step of RL algorithms. It accepts the environment, and the exploration strategy
    which wraps the policy.
    """

    def __init__(self, task, explorer, storage, num_workers=1):
        """
        Initialize the exploration phase.

        Args:
            task (Task, Env, tuple of Env and Policy): RL task or environment.
            explorer (Exploration): policies.
            storage (DictStorage): Rollout storage unit (=replay memory). It will save the rollouts in the storage
                while exploring.
            num_workers (int): number of processes / workers to run in parallel.
        """
        self.task = task
        self.explorer = explorer
        self.storage = storage
        self.num_workers = int(num_workers)

    ##############
    # Properties #
    ##############

    @property
    def task(self):
        """Return the RL task."""
        return self._task

    @task.setter
    def task(self, task):
        """Set the RL task."""
        if isinstance(task, (tuple, list)):
            env, policy = None, None
            for t in task:
                if isinstance(t, Env):
                    env = t
                if isinstance(t, Policy):  # TODO if multiple policies
                    policy = t
            if env is None or policy is None:
                raise ValueError("Expecting the task to be an instance of `RLTask` or a list/tuple of an environment "
                                 "and policy.")
            task = RLTask(env, policy)
        if not isinstance(task, RLTask):
            raise TypeError("Expecting the task to be an instance of `RLTask`, instead got: {}".format(type(task)))
        self._task = task

    @property
    def policy(self):
        """Return the policy."""
        return self.task.policy

    @property
    def env(self):
        """Return the environment."""
        return self.task.environment

    @property
    def explorer(self):
        """Return the exploration strategy."""
        return self._explorer

    @explorer.setter
    def explorer(self, explorer):
        """Set the exploration strategy."""
        if inspect.isclass(explorer):  # if it is a class
            explorer = explorer(self.policy)
        if not isinstance(explorer, Exploration):
            raise TypeError("Expecting explorer to be an instance of Exploration")
        self._explorer = explorer

    @property
    def storage(self):
        """Return the storage unit."""
        return self._storage

    @storage.setter
    def storage(self, storage):
        """Set the storage unit."""
        if not isinstance(storage, DictStorage):
            raise TypeError("Expecting the storage to be an instance of `DictStorage`, instead got: "
                            "{}".format(type(storage)))
        self._storage = storage

    ###########
    # Methods #
    ###########

    def explore(self, num_steps, rollout_idx=0, deterministic=False):
        """
        Explore the environment.

        Args:
            num_steps (int): number of steps
            deterministic (bool): if deterministic is True, then it does not explore in the environment.

        Returns:
            Rollout: memory storage
        """
        # reset environment
        observation = self.env.reset()
        print("\nExplorer - initial state: {}".format(observation))

        # reset storage
        self.storage.reset(init_states=observation, rollout_idx=rollout_idx)

        # reset explorer
        self.explorer.reset()

        # run RL task for T steps
        for step in range(num_steps):
            # get action and corresponding distribution from policy
            action, distribution = self.explorer.act(observation, deterministic=deterministic)

            # perform one step in the environment
            next_observation, reward, done, info = self.env.step(action)

            # insert in storage
            print("\nExplorer:")
            print("1. Observation data: {}".format(observation))
            print("2. Action data: {}".format(action))
            print("3. Next observation data: {}".format(next_observation))
            print("4. Reward: {}".format(reward))
            print("5. \\pi(.|s): {}".format(distribution))
            print("6. log \\pi(a|s): {}".format([d.log_prob(action) for d in distribution]))

            self.storage.insert(observation, action, next_observation, reward, mask=(1-done),
                                distributions=distribution, rollout_idx=rollout_idx)

            observation = next_observation
            if done:
                self.storage.end(rollout_idx)  # fill remaining mask values
                break

        # print("states: {}".format(self.storage['states']))
        print("actions: {}".format(self.storage['actions']))
        print("rewards: {}".format(self.storage['rewards']))
        # print("masks: {}".format(self.storage['masks']))
        # print("distributions: {}".format(self.storage['distributions']))
        raw_input('enter')

        # # clear explorer
        # self.explorer.clear()

        return self.storage

    #############
    # Operators #
    #############

    def __repr__(self):
        """Return a representation string about the class."""
        return self.__class__.__name__

    def __str__(self):
        """Return a string describing the class."""
        return self.__class__.__name__

    def __call__(self, num_steps, rollout_idx=0):
        """Explore in the environment with the specified number of time steps."""
        self.explore(num_steps, rollout_idx=rollout_idx)
