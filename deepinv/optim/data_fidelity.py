import torch
import torch.nn as nn


class DataFidelity(nn.Module):
    '''
    Data fidelity term for optimization algorithms.

    f(Ax,y)
    '''

    def __init__(self, f=None, grad_f=None, prox_f=None):
        super().__init__()
        self._grad_f = grad_f # TODO: use autograd?
        self._f = f
        self._prox_f = prox_f

    def f(self, x, y):
        return self._f(x)

    def grad_f(self, x, y):
        return self._grad_f(x, y)

    def prox_f(self, x, y, gamma):
        return self._prox_f(x, y, gamma)

    def forward(self, x, y, physics):
        Ax = physics.A(x)
        return self.f(Ax, y)

    def grad(self, x, y, physics):
        Ax = physics.A(x)
        if self.grad_f is not None:
            return self.grad_f(Ax, y)
        else:
            raise ValueError('No gradient defined for this data fidelity term.')

    def prox(self, x, y, physics, stepsize):
        if ['Denoising'] in physics.__class__.__name__:
            return self.prox_f(y, x, stepsize)
        else:# TODO: use GD?
            raise Exception("no prox operator is implemented for the data fidelity term.")


class L2(DataFidelity):
    '''
    L2 fidelity

    '''
    def __init__(self):
        super().__init__()

    def f(self, x, y):
        return (x-y).flatten().pow(2).sum()

    def grad_f(self, x, y):
        return x-y

    def prox(self, x, y, physics, stepsize):
        return physics.prox_l2(x, y, stepsize)


class PoissonLikelihood(DataFidelity):
    '''
    Poisson negative log likelihood
    Figueiredo Paper
    '''
    def __init__(self, bkg=0):
        super().__init__()
        self.bkg = bkg

    def f(self, x, y):
        return (- y * torch.log(x + self.bkg)).flatten().sum() + x.flatten().sum()

    def grad_f(self, x, y):
        return - y/(x+self.bkg) + x.numel()

    def prox_f(self, x, y, gamma):
        out = x - 1/gamma * ((x-1/gamma).pow(2) + 4*y/gamma).sqrt()
        return out/2


class L1(DataFidelity):
    '''
    L1 fidelity

    '''
    def __init__(self):
        super().__init__()

    def f(self, x, y):
        return (x - y).flatten().abs().sum()

    def grad_f(self, x, y):
        return torch.sign(x - y)

    def prox_f(self, x, y, gamma):
        # soft thresholding
        d = x-y
        aux = torch.sign(d)*torch.max(d.abs()-gamma, 0)
        return aux + y
