# -----------------------------------------------------------------------------
# QP/Python Library
#
# Port of Miro Samek's Quantum Framework to Python. The implementation takes
# the liberty to depart from Miro Samek's code where the specifics of desktop
# systems (compared to embedded systems) seem to warrant a different approach.
#
# Reference:
# Practical Statecharts in C/C++; Quantum Programming for Embedded Systems
# Author: Miro Samek, Ph.D.
# http://www.state-machine.com/
#
# -----------------------------------------------------------------------------
#
# Copyright (C) 2008-2014, Autolabel AB
# All rights reserved
# Author(s): Henrik Bohre (henrik.bohre@autolabel.se)
#
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions
#   are met:
#
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     - Neither the name of Autolabel AB, nor the names of its contributors
#       may be used to endorse or promote products derived from this
#       software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
#   THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#   INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
#   OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

"""Dining philosophers example"""

# Standard
from __future__ import with_statement
import sys
import os.path
sys.path.insert(0, os.path.join('..', '..'))
                                 # Expect us to be two levels below the library

# Local
import qp


HUNGRY_SIG = qp.USER_SIG
DONE_SIG = qp.USER_SIG + 1
EAT_SIG = qp.USER_SIG + 2
STOP_SIG = qp.USER_SIG + 3
TERMINATE_SIG = qp.USER_SIG + 4
MAX_PUB_SIG = qp.USER_SIG + 5

THINK_TIME = 7
EAT_TIME = 5
TIMEOUT_SIG = MAX_PUB_SIG

g_table = None
g_philosophers = None
g_state = None


class TableEvt(qp.Event):
    """Table event that targets a specific philosopher"""

    def __init__(self, sig):
        qp.Event.__init__(self, sig)
        self.phil_num = -1


class Table(qp.Active):
    """Table behavior - arbits the tableware resources"""

    signals = [
        HUNGRY_SIG,
        DONE_SIG,
        TERMINATE_SIG,
        STOP_SIG
    ]
    FREE = 0
    USED_LEFT = 1
    USED_RIGHT = 2

    def __init__(self, count):
        qp.Active.__init__(self, Table.initial)
        self.count = count
        self.fork_ = [Table.FREE] * self.count
        self.isHungry_ = [False] * self.count
        self.stoppedNums_ = 0

    def initial(self, e):
        print "Table.initial"
        self.INIT(Table.serving)

    def serving(self, e):
        if e.sig == HUNGRY_SIG:
            n = e.phil_num
            assert n < self.count and not self.isHungry_[n]
            displyPhilStat(n, "hungry")
            m = self.LEFT(n)
            if (self.fork_[m] == Table.FREE and self.fork_[n] == Table.FREE):
                self.fork_[m] = Table.USED_LEFT
                self.fork_[n] = Table.USED_RIGHT
                pe = TableEvt(EAT_SIG)
                pe.phil_num = n
                qp.QF.publish(pe)
                displyPhilStat(n, "eating")
            else:
                self.isHungry_[n] = True
            return 0
        elif e.sig == DONE_SIG:
            n = e.phil_num
            assert n < self.count
            self.fork_[self.LEFT(n)] = Table.FREE
            self.fork_[n] = Table.FREE
            displyPhilStat(n, "thinking")
            neighbor = self.RIGHT(n)  # check the right neighbor
            if (self.isHungry_[neighbor] and
                    self.fork_[neighbor] == Table.FREE):
                self.fork_[n] = Table.USED_LEFT
                self.fork_[neighbor] = Table.USED_RIGHT
                self.isHungry_[neighbor] = 0
                pe = TableEvt(EAT_SIG)
                pe.phil_num = neighbor
                qp.QF.publish(pe)
                displyPhilStat(neighbor, "eating")
            neighbor = self.LEFT(n)    # check the left neighbor
            if (self.isHungry_[neighbor] and
                    self.fork_[self.LEFT(neighbor)] == Table.FREE):
                self.fork_[self.LEFT(neighbor)] = Table.USED_LEFT
                self.fork_[neighbor] = Table.USED_RIGHT
                self.isHungry_[neighbor] = 0
                pe = TableEvt(EAT_SIG)
                pe.phil_num = neighbor
                qp.QF.publish(pe)
                displyPhilStat(neighbor, "eating")
            return 0
        elif e.sig == STOP_SIG:
            n = e.phil_num
            displyPhilStat(n, "stopped")
            self.stoppedNums_ += 1
            if self.stoppedNums_ == self.count:
                pe = qp.Event(TERMINATE_SIG)
                qp.QF.publish(pe)
            return 0
        elif e.sig == TERMINATE_SIG:
            print "received TERMINATE-SIG"
            self.stop()
            return 0
        return qp.Hsm.top

    # Non- methods

    def RIGHT(self, n):
        return (n + self.count - 1) % self.count

    def LEFT(self, n):
        return (n + 1) % self.count


class Philosopher(qp.Active):
    """Philosopher behavior"""
    signals = [
        EAT_SIG,
    ]

    def __init__(self, max_feed):
        qp.Active.__init__(self, Philosopher.initial)
        self.timeEvt_ = qp.TimeEvt(TIMEOUT_SIG)
        self.max_feed = max_feed

    def initial(self, e):
        print "Philosopher.initial"
        self.num_ = e.phil_num
        self.feedCtr_ = 0
        self.INIT(Philosopher.thinking)

    def thinking(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.timeEvt_.post_in(self, THINK_TIME)
            return 0
        elif e.sig == TIMEOUT_SIG:
            self.TRAN(Philosopher.hungry)
            return 0
        return qp.Hsm.top

    def hungry(self, e):
        if e.sig == qp.ENTRY_SIG:
            pe = TableEvt(HUNGRY_SIG)
            pe.phil_num = self.num_
            g_table.post_fifo(pe)
            return 0
        elif e.sig == EAT_SIG:
            if e.phil_num == self.num_:
                self.TRAN(Philosopher.eating)
                return 0
        return qp.Hsm.top

    def eating(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.feedCtr_ += 1    # one more feeding
            self.timeEvt_.post_in(self, EAT_TIME)
            return 0
        elif e.sig == qp.EXIT_SIG:
            pe = TableEvt(DONE_SIG)
            pe.phil_num = self.num_
            qp.QF.publish(pe)
            return 0
        elif e.sig == TIMEOUT_SIG:
            if (self.feedCtr_ < self.max_feed):
                self.TRAN(Philosopher.thinking)
            else:
                self.TRAN(Philosopher.final)
            return 0
        return qp.Hsm.top

    def final(self, e):
        if e.sig == qp.ENTRY_SIG:
            pe = TableEvt(STOP_SIG)
            pe.phil_num = self.num_
            qp.QF.publish(pe)
            self.stop()
            return 0
        return qp.Hsm.top


def displyPhilStat(n, stat):
    """Display  change of a philosopher"""
    with qp.QF._lock:
        global g_state
        if stat == "thinking":
            g_state[n] = " - "
        elif stat in ["eating", "hungry"]:
            g_state[n] = stat[:3]
        elif stat == "stopped":
            g_state[n] = " x "
        line = ""
        for index in range(g_table.count - 1, -1, -1):
            fork_state = g_table.fork_[index]
            if fork_state == Table.FREE:
                fork = '_'
            elif fork_state == Table.USED_LEFT:
                fork = '['
            else:
                fork = ']'
            line += \
                g_state[index] + ("%3d" % g_philosophers[index].feedCtr_) + fork
        prev = ""
        for s in g_state:
            assert not (s == "eat" and prev == "eat"), "Error"
            prev = s
        print "%4d %s" % (qp.QF.get_time(), line)


def terminate():
    e = qp.Event(TERMINATE_SIG)
    qp.QF.publish(e)


if __name__ == '__main__':
    import optparse
    import time
    parser = optparse.OptionParser()
    parser.add_option('--count', '-n', dest='count', default=10, type='int')
    parser.add_option('--maxfeed', dest='max_feed', default=200, type='int')
    parser.add_option('--time', dest='time', action='store_true',
                      default=False)
    opts, args = parser.parse_args()

    g_table = Table(count=opts.count)
    g_state = [" - "] * opts.count
    g_philosophers = [Philosopher(max_feed=opts.max_feed) \
                      for _n in range(opts.count)]
    start = time.time()
    for n, philosopher in enumerate(g_philosophers):
        ie = TableEvt(0)
        ie.phil_num = n
        philosopher.start(n + 1, 128, ie)
    g_table.start(opts.count + 1, 128, None)
    qp.QF.run()
    print "exiting..."
    if opts.time:
        print time.time() - start
