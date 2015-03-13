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

"""Python port of the Quantum Framework"""

# Standard
from __future__ import with_statement
import logging
import time
import threading
import Queue

# Local
import qp


QF_MAX_ACTIVE = 63          # maximum number of active objects
TICK = 10                   # milliseconds
TICK_S = TICK / 1000.0      # seconds

logger = logging.getLogger('qp')


class QueueOverflowError(Exception):
    pass


class QEQueue(Queue.Queue):
    """QEQueue base class"""

    def __init__(self, maxsize):
        Queue.Queue.__init__(self)
        self._max = 0            # watermark
        self._maxsize = maxsize

    def post_fifo(self, e):
        """Post event to queue in FIFO manner"""
        self._max = max(self._max, self.qsize())
        self.put(e, block=False)

    def post_lifo(self, e):
        """Post event to queue in LIFO manner"""
        raise NotImplementedError()


class Active(qp.Hsm):
    """Hierarchical state machine object with own thread and event queue"""

    signals = []

    class QThread(threading.Thread):
        """Wrapped python thread"""

        def __init__(self, active):
            threading.Thread.__init__(self)
            self._active = active

        def run(self):
            """Entry point for running Active object in own thread"""
            assert self._active != None
            self._active.run()

    def __init__(self, initial):
        qp.Hsm.__init__(self, initial)
        self._running = threading.Event()

    def start(self, prio, size, ie):
        """Start Active object at unique prio, and allocate space"""
        self._queue = QEQueue(size)
        self._prio = prio
        QF.add(self)
        for sig in self.signals:
            self.subscribe(sig)
        self.init(ie)
        self._thread = Active.QThread(self)
        self._thread.name = self.__class__.__name__
        self._thread.start()

    def post_fifo(self, e):
        """Post event to object's queue in FIFO manner.
        Raises QueueOverflowError if queue is full"""
        if self._queue.qsize() >= self._queue._maxsize:
            args = (self._thread.name, self._prio)
            message = 'Overflow in active object %s with prio %d' % args
            raise QueueOverflowError(message)
        self._queue.post_fifo(e)

    def post_lifo(self, e):
        """Post event to object's queue in LIFO manner"""
        raise NotImplementedError()

    def run(self):
        """Entry point for running Active object in own thread"""
        self._running.set()
        while self._running.isSet():
            e = self._queue.get()  # Get next event or hang on empty queue
            if e is None:  # Reached sentinel value
                break
            qp.Hsm.dispatch(self, e)
        self.unsubscribe_all()
        QF.remove(self)

    def stop(self):
        """Stop object from running and receiving events"""
        self._running.clear()
        self._queue.put(None)  # Insert sentinel value

    def subscribe(self, sig):
        """Subscribe to specified signal"""
        p = self._prio
        assert sig >= qp.USER_SIG and 0 < p <= QF_MAX_ACTIVE and \
            QF._active[p] == self
        with QF._lock:
            if sig in QF._subscribers:
                if not p in QF._subscribers[sig]:
                    QF._subscribers[sig].append(p)
            else:
                QF._subscribers[sig] = [p]
            QF._subscribers[sig].sort()

    def unsubscribe(self, sig):
        """Unsubscribe to specified signal"""
        p = self._prio
        assert 0 < p <= QF_MAX_ACTIVE and QF._active[p] == self
        with QF._lock:
            QF._subscribers[sig].remove(p)

    def unsubscribe_all(self):
        """Unsubscribe to all signals"""
        p = self._prio
        assert 0 < p <= QF_MAX_ACTIVE and QF._active[p] == self
        with QF._lock:
            for subscribers in QF._subscribers.itervalues():
                if p in subscribers:
                    subscribers.remove(p)


class TimeEvt(qp.Event):
    """Timer event"""

    def __init__(self, s):
        assert s >= qp.USER_SIG
        self.sig = s
        self._act = None
        self._ctr = 0
        self._interval = 0
        self.ts = time.time()

    def post_in(self, act, ticks):
        """Post event to specified Active object"""
        self._interval = 0
        self._arm(act, ticks)

    def publish_in(self, ticks):
        """Publish to framework"""
        self._interval = 0
        self._arm(None, ticks)

    def post_every(self, act, ticks):
        """Post event in specified Active object at interval"""
        self._interval = ticks
        self._arm(act, ticks)

    def publish_every(self, ticks):
        """Publish event to framework at interval"""
        self._interval = ticks
        self._arm(None, ticks)

    def disarm(self):
        """Disable timer event"""
        with QF._lock:
            was_armed = False
            while self in QF._time_evt_list:
                QF._time_evt_list.remove(self)    # Remove us from the list
                was_armed = True
        return was_armed

    def rearm(self, ticks):
        """Rearm timer event"""
        assert ticks > 0 and self.sig >= qp.USER_SIG
        with QF._lock:
            self._ctr = ticks
            if self in QF._time_evt_list:    # Are we armed
                is_armed = True
            else:
                is_armed = False
                QF._time_evt_list.append(self)
        return is_armed

    def _arm(self, act, ticks):
        """Arm timer event"""
        assert ticks > 0 and self.sig >= qp.USER_SIG
        self._ctr = ticks
        self._act = act
        with QF._lock:
            QF._time_evt_list.append(self)    # Add us to the list


class QF(object):
    """Framework for running hierarchical FSMs as Active objects.
    This implementation only allows a single QF instance in an application."""

    _active = [None] * (QF_MAX_ACTIVE + 1)
    _lock = threading.RLock()
    _time_evt_list = []
    _subscribers = {}  # Dict with signals: subscriber list
    _tick_ctr = 0
    _running = False

    @classmethod
    def start(cls):
        """Start the framework"""
        cls._running = True

    @classmethod
    def run(cls):
        """Run framework"""
        cls.start()
        while cls._running:
            with cls._lock:
                cls.tick()
            time.sleep(TICK_S)

    @classmethod
    def stop(cls):
        """Stop framework"""
        cls._running = False

    @classmethod
    def publish(cls, e):
        """Publish event e to the framework"""
        with cls._lock:  # perform multicasting with the scheduler locked
            subscribers = cls._subscribers.get(e.sig, [])
            for p in subscribers:
                assert cls._active[p] != None
                cls._active[p].post_fifo(e)

    @classmethod
    def tick(cls):
        """Update system tick and evaluate counters and timer events"""
        cls._tick_ctr += 1    # increment the tick counter
        # iterate over copy of list since we change it
        for t in cls._time_evt_list[:]:
            t._ctr -= 1
            if (t._ctr == 0):    # is the time event about to expire?
                if (t._interval != 0):    # is it a periodic time evt?
                    t._ctr = t._interval
                else:  # one-shot timeevt, disarm by removing it from the list
                    assert t in cls._time_evt_list
                    cls._time_evt_list.remove(t)
                t.ts = time.time()
                if (t._act != None):
                    t._act.post_fifo(t)
                else:
                    cls.publish(t)

    @classmethod
    def get_time(cls):
        """Return tick counter"""
        with cls._lock:
            tick_ctr = cls._tick_ctr
        return tick_ctr

    @classmethod
    def get_queue_margin(cls, prio):
        assert prio <= QF_MAX_ACTIVE and cls._active[prio] != 0
        with cls._lock:
            margin = cls._active[prio]._queue._maxsize - \
                     cls._active[prio]._queue._max
        return margin

    @classmethod
    def print_queue_margins(cls):
        s = 'QF HWMS: '
        for active in cls._active:
            if active is not None:
                s += ("%s[%s]=%s(%s) " % (active._thread.name,
                                          active._prio,
                                          active._queue.qsize(),
                                          active._queue._max))
        return s

    @classmethod
    def get_queue_margins(cls):
        """Return string of active objects sorted on max queue"""
        stats = []
        with cls._lock:
            for active in cls._active:
                if active is not None:
                    stats.append((active._thread.name,
                                  active._prio,
                                  active._queue._max))
        queues = ['%s[%s]=%s' % s for s in sorted(stats,
                                                  key=lambda x: x[2],
                                                  reverse=True)]
        return ', '.join(queues)

    @classmethod
    def clear_queuemargins(cls):
        with cls._lock:
            for active in cls._active:
                if active is not None:
                    active._queue._max = 0

    @classmethod
    def add(cls, a):
        """Add active object"""
        p = a._prio
        assert 0 < p <= QF_MAX_ACTIVE and (cls._active[p] == None), \
            "p=%d" % (p)
        cls._active[p] = a

    @classmethod
    def remove(cls, a):
        """Remove active object"""
        with cls._lock:
            p = a._prio
            assert 0 < p <= QF_MAX_ACTIVE
            cls._active[p] = None        # free-up the priority level
            logger.info('Removing %s' % a._thread.name)
            for active in cls._active:
                if active:  # At least one active object
                    return
            # No more active objects - stopping framework
            logger.info('No more active objects - shutting down framework')
            cls.stop()
