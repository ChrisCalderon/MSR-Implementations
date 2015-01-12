#An implementation of Abe Othman's MSR, as defined in his paper "Profit-Charging Market Makers with Bounded Loss, Vanishing Bid/Ask Spreads, and Unlimited Market Depth."
#    Copyright (C) 2015  Chris Calderon
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#Questions can be sent to chris-da-dev@augur.net .
import math
import pylab
import random

def u(s):
    '''utility function'''
    return math.log(s)

def g(s):
    '''profit function'''
    return 0.01*s

def f(s):
    '''liquidity function'''
    return .924*((s + 132.3)**0.5 - 132.3**0.5)

def d(x, y):
    '''L1 norm a.k.a. taxi cab metric'''
    return sum(abs(x_i-y_i) for x_i, y_i in zip(x, y))

def C(x, ps, s, x0):
    '''Implicitly solve the Cost function with a binary
    search on equation 4.2 of the paper'''
    f_s = f(s)

    def left_side(C_x):
        #
        #----
        #\
        #/     p_i*u(C(x) - x_i + f_s) = u(x0 + f_s)
        #----
        # i
        #
        # A lower bound for C(x) is max(x_i) - f_s.
        # Proof:
        # u : R+ -> R implies that C(x) - x_i + f_s > 0
        # therefore, C(x) > x_i - f_s for every x_i. Therefore,
        # C(x) > max(x_i) - f_s. Q.E.D.
        #
        result = 0
        for p_i, x_i in zip(ps, x):
            result += p_i*u(C_x - x_i + f_s)
        return result

    right_side = u(x0 + f_s)
    #lower_bound = min(x) + x0 # maybe these bounds are incorrect?
    lower_bound = max(x) - f_s
    upper_bound = max(x) + x0 + f_s
    approx = (lower_bound + upper_bound)/2
    left_side_approx = left_side(approx)
    eps = 1e-8
    steps = 1
    # binary search
    while abs(right_side - left_side_approx) > eps:
        if lower_bound == upper_bound:
            raise ValueError(
                "Failed to converge! stuck at %f, off by %f after %d steps" % (
                    approx, right_side - left_side_approx, steps))
        if left_side_approx > right_side:
            upper_bound = approx
        else:
            lower_bound = approx
        approx = (lower_bound + upper_bound)/2
        left_side_approx = left_side(approx)
        steps += 1

    return approx, g(s), f_s

def abe_msr(x, y, ps, x0, s):
    Cx, gs, fs = C(x, ps, s, x0)
    Cy, gsd, fsd = C(y, ps, s + d(x,y), x0)
    return Cy - Cx, gsd - gs, fsd - fs

def inc_i(x, i):
    # returns a vector a single step in the +ith direction from x
    x_ = x[:]
    x_[i] += 1
    return x_

def make_plot(odds, point, s, x0=100):
    # Plots the change in the price of a fixed size bet
    # while varying s (market volume/ distance the payout vector
    # has been moved by trades)

    price_sum = [0] * len(s) # an array to keep track of the sum of the prices

    # set the axis labels on the plot
    pylab.xlabel('$s$ ~ Volume') 
    pylab.ylabel('$M(\mathbf{x}, \mathbf{y})$ ~ Price Per Share')
    # we vary each dimension of the point...
    for i in range(len(point)):
        point_i = inc_i(point, i) # ... by incrementing the ith value.
        label = '%s -> %s' % (tuple(point), tuple(point_i)) # label for the ith curve
        prices = [sum(abe_msr(point, point_i, odds, x0, si)) for si in s] # calculate price for varying s
        for j, pi in enumerate(prices):
            price_sum[j] += pi # add the price with each s to the price sum
        pylab.semilogx(s, prices, label=label) # plot the curve
    pylab.semilogx(s, price_sum, label='sum') # plot the sum
    pylab.legend(loc=5) # create and set the legend location
    fname = 'odds - %s; x = %s, x0 = %d.png' % (tuple(odds), tuple(point), x0) # give a descriptive filename
    pylab.title(fname)
    pylab.savefig(fname)
    pylab.close()

def random_point(length, max):
    return [random.randrange(max) for _ in range(length)]

if __name__ == '__main__':
    oddses = [[.5,.5], [.85,.15]]
    point = [0, 0]
    s = [10**(3.*i/50) for i in range(101)]
    for i, odds in enumerate(oddses):
        make_plot(odds, point, s, 10)
        make_plot(odds, point, s, 100)
        make_plot(odds, point, s, 1000)

    oddses = [[.5, .3, .2], [.3, .25, .2, .15, .1]]
    for odds in oddses:
        point = random_point(len(odds), 100)
        make_plot(odds, point, s)