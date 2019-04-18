#!/usr/bin/env python
"""Defines the policy losses in RL.
"""

import torch

from pyrobolearn.losses import BatchLoss
from pyrobolearn.returns.estimators import Estimator


__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class PGLoss(BatchLoss):
    r"""Policy Gradient Loss

    Compute the policy gradient loss which is maximized and given by:

    .. math:: L^{PG} = \mathbb{E}[ \log \pi_{\theta}(a_t | s_t) \psi_t ]

     where :math:`\psi_t` is the associated return estimator, which can be for instance, the total reward estimator
     :math:`\psi_t = R(\tau)` (where :math:`\tau` represents the whole trajectory), the state action value estimator
     :math:`\psi_t = Q(s_t, a_t)`, or the advantage estimator :math:`\psi_t = A_t = Q(s_t, a_t) - V(s_t)`. Other
     returns are also possible.

    The gradient with respect to the parameters :math:`\theta` is then given by:

    .. math:: g = \mathbb{E}[ \nabla_{\theta} \log \pi_{\theta}(a_t | s_t) \psi_t ]

    References:
        [1] "Proximal Policy Optimization Algorithms", Schulman et al., 2017
        [2] "High-Dimensional Continuous Control using Generalized Advantage Estimation", Schulman et al., 2016
    """

    def __init__(self, estimator):
        """
        Initialize the Policy Gradient loss.

        Args:
            estimator (Estimator): estimator/return that has been used on the rollout storage / batch.
        """
        super(PGLoss, self).__init__()
        if not isinstance(estimator, Estimator):
            raise TypeError("The given estimator is not an instance of `Estimator`, instead got: "
                            "{}".format(type(estimator)))
        self._estimator = estimator

    def _compute(self, batch):
        """
        Compute the PG loss on the given batch.

        Args:
            batch (Batch): batch containing the states, actions, rewards, etc.

        Returns:
            torch.Tensor: loss scalar value
        """
        # evaluate the action
        log_curr_pi = batch.current['action_distributions']
        log_curr_pi = log_curr_pi.log_probs(batch.current['actions'])
        estimator = batch[self._estimator]

        # compute loss and return it
        loss = torch.exp(log_curr_pi) * estimator
        return -loss.mean()

    def latex(self):
        """Return a latex formula of the loss."""
        return r"\mathbb{E}[ r_t(\theta) A_t ]"


class CPILoss(BatchLoss):
    r"""CPI Loss

    Conservative Policy Iteration objective which is maximized and defined in [1]:

    .. math:: L^{CPI}(\theta) = \mathbb{E}[ r_t(\theta) A_t ]

    where the expectation is taken over a finite batch of samples, :math:`A_t` is an estimator of the advantage fct at
    time step :math:`t`, :math:`r_t(\theta)` is the probability ratio given by
    :math:`r_t(\theta) = \frac{ \pi_{\theta}(a_t|s_t) }{ \pi_{\theta_{old}}(a_t|s_t) }`.

    References:
        [1] "Approximately optimal approximate reinforcement learning", Kakade et al., 2002
        [2] "Proximal Policy Optimization Algorithms", Schulman et al., 2017
    """

    def __init__(self, estimator):
        """
        Initialize the CPI Loss.

        Args:
            estimator (Estimator): estimator that has been used on the rollout storage / batch.
        """
        super(CPILoss, self).__init__()
        if not isinstance(estimator, Estimator):
            raise TypeError("The given estimator is not an instance of `Estimator`, instead got: "
                            "{}".format(type(estimator)))
        self._estimator = estimator

    def _compute(self, batch):
        """
        Compute the CPI loss on the given batch.

        Args:
            batch (Batch): batch containing the states, actions, rewards, etc.

        Returns:
            torch.Tensor: loss scalar value
        """
        # ratio = policy_distribution / old_policy_distribution
        log_curr_pi = batch.current['action_distributions']
        log_curr_pi = log_curr_pi.log_probs(batch.current['actions'])
        log_prev_pi = batch['action_distributions']
        log_prev_pi = log_prev_pi.log_probs(batch['actions'])

        ratio = torch.exp(log_curr_pi - log_prev_pi)
        estimator = batch[self._estimator]

        loss = ratio * estimator
        return -loss.mean()

    def latex(self):
        """Return a latex formula of the loss."""
        return r"\mathbb{E}[ r_t(\theta) A_t ]"


class CLIPLoss(BatchLoss):
    r"""CLIP Loss

    Loss defined in [1] which is maximized and given by:

    .. math:: L^{CLIP}(\theta) = \mathbb{E}[ \min(r_t(\theta) A_t, clip(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t) ]

    where the expectation is taken over a finite batch of samples, :math:`A_t` is an estimator of the advantage fct at
    time step :math:`t`, :math:`r_t(\theta)` is the probability ratio given by
    :math:`r_t(\theta) = \frac{ \pi_{\theta}(a_t|s_t) }{ \pi_{\theta_{old}}(a_t|s_t) }`.

    References:
        [1] "Proximal Policy Optimization Algorithms", Schulman et al., 2017
    """

    def __init__(self, estimator, clip=0.2):
        """
        Initialize the loss.

        Args:
            estimator (Estimator): estimator that has been used on the rollout storage / batch.
            clip (float): clip parameter
        """
        super(CLIPLoss, self).__init__()
        self.eps = clip
        if not isinstance(estimator, Estimator):
            raise TypeError("The given estimator is not an instance of `Estimator`, instead got: "
                            "{}".format(type(estimator)))
        self._estimator = estimator

    def _compute(self, batch):
        """
        Compute the CLIP loss on the given batch.

        Args:
            batch (Batch): batch containing the states, actions, rewards, etc.

        Returns:
            torch.Tensor: loss scalar value
        """
        log_curr_pi = batch.current['action_distributions']
        log_curr_pi = log_curr_pi.log_probs(batch.current['actions'])
        log_prev_pi = batch['action_distributions']
        log_prev_pi = log_prev_pi.log_probs(batch['actions'])

        ratio = torch.exp(log_curr_pi - log_prev_pi)
        estimator = batch[self._estimator]

        loss = torch.min(ratio * estimator, torch.clamp(ratio, 1.0-self.eps, 1.0+self.eps) * estimator)
        return -loss.mean()

    def latex(self):
        """Return a latex formula of the loss."""
        return r"\mathbb{E}[ \min(r_t(\theta) A_t, clip(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t) ]"


class KLPenaltyLoss(BatchLoss):
    r"""KL Penalty Loss

    KL Penalty to minimize:

    .. math:: L^{KL}(\theta) = \mathbb{E}[ KL( \pi_{\theta_{old}}(a_t | s_t) || \pi_{\theta}(a_t | s_t) ) ]

    where :math:`KL(.||.)` is the KL-divergence between two probability distributions.
    """

    def __init__(self):
        """
        Initialize the KL Penalty loss.
        """
        super(KLPenaltyLoss, self).__init__()
        # self.p = p
        # self.q = q

    def _compute(self, batch):
        """
        Compute the KL divergence loss: :math:`KL(p||q)`.

        Args:
            batch (Batch): batch containing the states, actions, rewards, etc.

        Returns:
            torch.Tensor: loss scalar value
        """
        curr_pi = batch.current['action_distributions']
        prev_pi = batch['action_distributions']

        return torch.distributions.kl.kl_divergence(prev_pi, curr_pi).mean()

    def latex(self):
        """Return a latex formula of the loss."""
        return r"\mathbb{E}[ KL( \pi_{\theta_{old}}(a_t | s_t) || \pi_{\theta}(a_t | s_t) ) ]"


class EntropyLoss(BatchLoss):
    r"""Entropy Loss

    Entropy loss, which is used to ensure sufficient exploration when maximized [1,2,3]:

    .. math:: L^{Entropy}(\theta) = H[ \pi_{\theta} ]

    where :math:`H[.]` is the Shannon entropy of the given probability distribution.

    References:
        [1] "Simple Statistical Gradient-following Algorithms for Connectionist Reinforcement Learning", Williams, 1992
        [2] "Asynchronous Methods for Deep Reinforcement Learning", Mnih et al., 2016
        [3] "Proximal Policy Optimization Algorithms", Schulman et al., 2017
    """

    def __init__(self):
        """
        Initialize the entropy loss.
        """
        super(EntropyLoss, self).__init__()

    def _compute(self, batch):
        """
        Compute the entropy loss.

        Args:
            batch (Batch): batch containing the states, actions, rewards, etc.

        Returns:
            torch.Tensor: loss scalar value
        """
        distribution = batch.current['action_distributions']
        entropy = distribution.entropy().mean()
        return entropy