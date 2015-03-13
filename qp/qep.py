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

"""Python port of the Quantum Event Processor"""

# Internal QEP constants
_QEP_EMPTY_SIG = 0
_QEP_MAX_NEST_DEPTH = 6

# QEP reserved signals
ENTRY_SIG = 1
EXIT_SIG = 2
INIT_SIG = 3
TERM_SIG = 4
USER_SIG = 4


class Event(object):
    """Event base class"""

    def __init__(self, sig=0):
        self.sig = sig


_QEP_EMPTY_EVENT = Event(_QEP_EMPTY_SIG)
_QEP_ENTRY_EVENT = Event(ENTRY_SIG)
_QEP_EXIT_EVENT = Event(EXIT_SIG)
_QEP_INIT_EVENT = Event(INIT_SIG)
_QEP_RESERVED_EVENTS = [
    _QEP_EMPTY_EVENT,
    _QEP_ENTRY_EVENT,
    _QEP_EXIT_EVENT,
    _QEP_INIT_EVENT,
]

Q_TRAN_NONE_TYPE = 0
Q_TRAN_DYN_TYPE = 1
Q_TRAN_STA_TYPE = 2

QEP_MAX_NEST_DEPTH = 6


class Fsm(object):
    """Fsm represents a flat state machine with entry/exit actions"""

    def __init__(self, initial=None):
        self._state = initial    # Current active state
        # Transition attributes (none/dynamic/static)
        self.tran_ = Q_TRAN_NONE_TYPE

    def init(self, e=None):
        """Performs the first step of FSM initialization by assigning the
        initial pseudostate to the currently active state of the state
        machine """
        assert self._state != None
        initial = self._state

        self.initial(e)        # Execute the initial transition
        assert initial != self._state    # The target cannot be initial
        self._state(self, _QEP_ENTRY_EVENT)

    def initial(self, e):
        """Pure virtual initial function"""
        raise NotImplementedError("Must override this function")

    def dispatch(self, e):
        """Processes one event at a time in Run-to-Completion fashion.
        The argument e is a Event or a class derived from Event.

        Note: Must be called after Fsm.init()."""
        s = self._state
        s(self, e)
        if (self.tran_ != Q_TRAN_NONE_TYPE):
            s(self, _QEP_EXIT_EVENT)    # Exit the source
            self._state(self, _QEP_ENTRY_EVENT)  # Enter target
            self.tran_ = Q_TRAN_NONE_TYPE     # get ready for next transition

    def get_state(self):
        """Returns current active state of a FSM. Note that this should be
        used only inside state handler functions"""
        return self._state


class Hsm(Fsm):
    """Hsm represents an hierarchical finite state machine (HSM)"""

    def __init__(self, initial):
        Fsm.__init__(self, initial)

    def top(self, e=None):
        """the ultimate root of state hierarchy in all HSMs
        derived from Hsm. This state handler always returns (QSTATE)0,
        which means that it handles all events."""
        return 0

    def init(self, e=None):
        """Performs the first step of HSM initialization by assigning the
        initial pseudostate to the currently active state of the state
        machine """
        assert self._state != 0

        s = Hsm.top    # An HSM starts in the top state
        self._state(self, e)    # Take top-most initial transition
        while True:        # Drill into the target...
            t = self._state
            path = [t]    # Transition path from top to init state
            t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)
            while (t != s):
                path.insert(0, t)
                t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)
            # Entry path must not overflow
            assert len(path) <= QEP_MAX_NEST_DEPTH

            for t in path:        # Retrace the entry path in reverse
                self.QEP_TRIG_(t, ENTRY_SIG)

            s = self._state
            if self.QEP_TRIG_(s, INIT_SIG) != 0:
                break

    def dispatch(self, e):
        """Executes state handlers for dispatched signals"""
        t = self._state
        path = [None] * QEP_MAX_NEST_DEPTH
        path[2] = t
        while (t != 0):    # Process the event hierarchically
            s = t
            t = s(self, e)    # Invoke signal handler

        if (self.tran_ != Q_TRAN_NONE_TYPE):            # transition taken?
            path[0] = self._state    # save the transition target
            self._state = path[2]          # restore current state
            path[1] = s                    # save the transition source

            s = path[2]
            # Exit current state to the transition source path[1]
            while s != path[1]:
                t = self.QEP_TRIG_(s, EXIT_SIG)
                if t != 0:
                    s = t
                else:
                    # Find out the superstate
                    s = self.QEP_TRIG_(s, _QEP_EMPTY_SIG)

            # dynamic transition
            s = path[2]    # save the transition source
            path = self.exec_tran(path)
            self.tran_ = Q_TRAN_NONE_TYPE   # clear the attribute for next use

    def is_in(self, state):
        """Tests if a given state is part of the current active state
        configuration"""
        s = self._state
        while s != state:
            s = self.QEP_TRIG_(s, _QEP_EMPTY_SIG)
            if s == 0:
                return 0
        return 1

    def exec_tran(self, path):
        """Helper function to execute HSM transition"""
        t = path[0]
        src = path[1]
        ip = -1        # transition entry path index

        if (src == t):    # (a) check source == target (tran to self)
            self.QEP_TRIG_(src, EXIT_SIG)            # exit the source
            ip = ip + 1                             # enter the target
        else:
                                        # put superstate of target in t
            t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)
            if (src == t):            # (b) check source == target->super
                ip = ip + 1                            # enter the target
            else:
                                        # put superstate of source into s
                s = self.QEP_TRIG_(src, _QEP_EMPTY_SIG)
                if (s == t):    # (c) check source->super == target->super
                    self.QEP_TRIG_(src, EXIT_SIG)
                    ip = ip + 1
                else:
                    if (s == path[0]):    # (d) check source->super == target
                        self.QEP_TRIG_(src, EXIT_SIG)
                    else:   # (e) check rest of source == target->super->super
                        iq = 0            # LCA not found
                        ip = ip + 2            # enter the target
                        path[ip] = t    # enter the superstate of target
                        t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)
                        while (t != 0):
                            ip = ip + 1
                            path[ip] = t    # store the entry path
                            if (t == src):    # is it the source
                                iq = 1        # indicate that the LCA is found
                                assert ip < _QEP_MAX_NEST_DEPTH
                                ip = ip - 1
                                t = 0
                            else:    # it is not the source, keep going up
                                t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)

                        if (iq == 0):        # the LCA not found yet?
                            assert ip < _QEP_MAX_NEST_DEPTH
                            self.QEP_TRIG_(src, EXIT_SIG)  # exit the source
                                    # (f) check the rest of source->super...
                                    # == target->super->super...
                            iq = ip
                            while True:
                                if (s == path[iq]):    # is s the LCA?
                                    t = s    # indicate that the LCA is found
                                    ip = iq - 1    # do not enter LCA
                                    iq = -1    # terminate the loop
                                else:
                                    iq = iq - 1  # lower superstate of target
                                if (iq >= 0):
                                    pass
                                else:
                                    break

                            if (t == 0):    # the LCA not found yet?
                                # (g) check each source->super->...
                                # for each target->super...
                                while True:
                                    t = self.QEP_TRIG_(s, EXIT_SIG)  # exit s
                                    if (t != 0):    # exit not handled?
                                        s = t        # t points to superstate
                                    else:            # exit action handled
                                        s = self.QEP_TRIG_(s, _QEP_EMPTY_SIG)
                                    iq = ip
                                    while True:
                                        if (s == path[iq]):  # is the LCA?
                                            # do not enter the LCA
                                            ip = iq - 1
                                            iq = -1     # break inner loop
                                            s = 0        # and the outer loop
                                        else:
                                            iq = iq - 1
                                        if (iq >= 0):
                                            pass
                                        else:
                                            break
                                    if (s != 0):
                                        pass
                                    else:
                                        break

                        # retrace the entry path in reverse (desired) order
        entry_path = path[:ip + 1]
        for t in reversed(entry_path):
            self.QEP_TRIG_(t, ENTRY_SIG)
        s = path[0]
        self._state = s

        while (self.QEP_TRIG_(s, INIT_SIG) == 0):    # drill into the target
            t = self._state
            path[0] = t
            ip = 0
            t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)
            while (t != s):
                ip = ip + 1
                path[ip] = t
                t = self.QEP_TRIG_(t, _QEP_EMPTY_SIG)

            assert ip < _QEP_MAX_NEST_DEPTH

            # retrace the entry path in reverse (correct) order
            entry_path = path[:ip + 1]
            for t in reversed(entry_path):
                self.QEP_TRIG_(t, ENTRY_SIG)
            s = self._state

    def INIT(self, target):
        """Perform init transition"""
        self._state = target

    def TRAN(self, target):
        """Perform normal transition"""
        self.tran_ = Q_TRAN_DYN_TYPE
        self._state = target

    def QEP_TRIG_(self, state, signal):
        return state(self, _QEP_RESERVED_EVENTS[signal])
