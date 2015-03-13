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

"""Test event processor"""

# Standard
import sys
sys.path.insert(0, '..')
import string
import unittest

# Local
import qp

A_SIG = qp.USER_SIG
B_SIG = qp.USER_SIG + 1
C_SIG = qp.USER_SIG + 2
D_SIG = qp.USER_SIG + 3
E_SIG = qp.USER_SIG + 4
F_SIG = qp.USER_SIG + 5
G_SIG = qp.USER_SIG + 6
H_SIG = qp.USER_SIG + 7
I_SIG = qp.USER_SIG + 8
TERMINATE_SIG = qp.USER_SIG + 9
IGNORE_SIG = qp.USER_SIG + 10
MAX_SIG = qp.USER_SIG + 11


EXPECTED_STRING = \
"""top-INIT;d-ENTRY;d2-ENTRY;d2-INIT;d21-ENTRY;d211-ENTRY;
A:d21-A;d211-EXIT;d21-EXIT;d21-ENTRY;d21-INIT;d211-ENTRY;
B:d21-B;d211-EXIT;d211-ENTRY;
D:d211-D;d211-EXIT;d21-INIT;d211-ENTRY;
E:d-E;d211-EXIT;d21-EXIT;d2-EXIT;d1-ENTRY;d11-ENTRY;
I:d1-I;
F:d1-F;d11-EXIT;d1-EXIT;d2-ENTRY;d21-ENTRY;d211-ENTRY;
I:d2-I;
I:d-I;
F:d2-F;d211-EXIT;d21-EXIT;d2-EXIT;d1-ENTRY;d11-ENTRY;
A:d1-A;d11-EXIT;d1-EXIT;d1-ENTRY;d1-INIT;d11-ENTRY;
B:d1-B;d11-EXIT;d11-ENTRY;
D:d1-D;d11-EXIT;d1-EXIT;d-INIT;d1-ENTRY;d11-ENTRY;
D:d11-D;d11-EXIT;d1-INIT;d11-ENTRY;
E:d-E;d11-EXIT;d1-EXIT;d1-ENTRY;d11-ENTRY;
G:d11-G;d11-EXIT;d1-EXIT;d2-ENTRY;d21-ENTRY;d211-ENTRY;
H:d211-H;d211-EXIT;d21-EXIT;d2-EXIT;d-INIT;d1-ENTRY;d11-ENTRY;
H:d11-H;d11-EXIT;d1-EXIT;d-INIT;d1-ENTRY;d11-ENTRY;
C:d1-C;d11-EXIT;d1-EXIT;d2-ENTRY;d2-INIT;d21-ENTRY;d211-ENTRY;
G:d21-G;d211-EXIT;d21-EXIT;d2-EXIT;d1-ENTRY;d1-INIT;d11-ENTRY;
C:d1-C;d11-EXIT;d1-EXIT;d2-ENTRY;d2-INIT;d21-ENTRY;d211-ENTRY;
C:d-C;d211-EXIT;d21-EXIT;d2-EXIT;d-EXIT;s-ENTRY;s-INIT;s1-ENTRY;s11-ENTRY;
C:s1-C;s11-EXIT;s1-EXIT;s2-ENTRY;s2-INIT;s21-ENTRY;s211-ENTRY;
A:s21-A;s211-EXIT;s21-EXIT;s21-ENTRY;s21-INIT;s211-ENTRY;
A:s21-A;s211-EXIT;s21-EXIT;s21-ENTRY;s21-INIT;s211-ENTRY;
B:s21-B;s211-EXIT;s211-ENTRY;
B:s21-B;s211-EXIT;s211-ENTRY;
D:s211-D;s211-EXIT;s21-INIT;s211-ENTRY;
D:s211-D;s211-EXIT;s21-INIT;s211-ENTRY;
E:s-E;s211-EXIT;s21-EXIT;s2-EXIT;s1-ENTRY;s11-ENTRY;
I:s1-I;
F:s1-F;s11-EXIT;s1-EXIT;s2-ENTRY;s21-ENTRY;s211-ENTRY;
I:s2-I;
I:s-I;
F:s2-F;s211-EXIT;s21-EXIT;s2-EXIT;s1-ENTRY;s11-ENTRY;
A:s1-A;s11-EXIT;s1-EXIT;s1-ENTRY;s1-INIT;s11-ENTRY;
A:s1-A;s11-EXIT;s1-EXIT;s1-ENTRY;s1-INIT;s11-ENTRY;
B:s1-B;s11-EXIT;s11-ENTRY;
B:s1-B;s11-EXIT;s11-ENTRY;
D:s1-D;s11-EXIT;s1-EXIT;s-INIT;s1-ENTRY;s11-ENTRY;
D:s11-D;s11-EXIT;s1-INIT;s11-ENTRY;
D:s1-D;s11-EXIT;s1-EXIT;s-INIT;s1-ENTRY;s11-ENTRY;
D:s11-D;s11-EXIT;s1-INIT;s11-ENTRY;
E:s-E;s11-EXIT;s1-EXIT;s1-ENTRY;s11-ENTRY;
G:s11-G;s11-EXIT;s1-EXIT;s2-ENTRY;s21-ENTRY;s211-ENTRY;
H:s211-H;s211-EXIT;s21-EXIT;s2-INIT;s21-ENTRY;s211-ENTRY;
G:s21-G;s211-EXIT;s21-EXIT;s2-EXIT;s1-ENTRY;s1-INIT;s11-ENTRY;
H:s11-H;s11-EXIT;s1-EXIT;s-INIT;s1-ENTRY;s11-ENTRY;
F:s1-F;s11-EXIT;s1-EXIT;s2-ENTRY;s21-ENTRY;s211-ENTRY;
H:s211-H;s211-EXIT;s21-EXIT;s2-INIT;s21-ENTRY;s211-ENTRY;
F:s2-F;s211-EXIT;s21-EXIT;s2-EXIT;s1-ENTRY;s11-ENTRY;
C:s1-C;s11-EXIT;s1-EXIT;s2-ENTRY;s2-INIT;s21-ENTRY;s211-ENTRY;
G:s21-G;s211-EXIT;s21-EXIT;s2-EXIT;s1-ENTRY;s1-INIT;s11-ENTRY;
G:s11-G;s11-EXIT;s1-EXIT;s2-ENTRY;s21-ENTRY;s211-ENTRY;"""


class HsmTst(qp.Hsm):
    """Test all possible transitions in a hierarchical state machine"""

    def __init__(self):
        qp.Hsm.__init__(self, HsmTst.initial)
        self.foo_ = None
        self.result = ""  # Contains info about state transitions

    def initial(self, e):
        """Initial top level init transition"""
        self._add_message("top-INIT;")
        self.foo_ = 0
        self.INIT(HsmTst.d2)

    def d(self, e):
        """d state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("d-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("d-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("d-INIT;")
            self.INIT(HsmTst.d11)
            return 0
        elif e.sig == C_SIG:
            self._add_message("d-C;")
            self.TRAN(HsmTst.s)
            return 0
        elif e.sig == E_SIG:
            self._add_message("d-E;")
            self.TRAN(HsmTst.d11)
            return 0
        elif e.sig == I_SIG:
            if self.foo_:
                self._add_message("d-I;")
                self.foo_ = 0
                return 0
        elif e.sig == TERMINATE_SIG:
            sys.exit()
            return 0
        return qp.Hsm.top

    def d1(self, e):
        """d1 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("d1-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("d1-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("d1-INIT;")
            self.INIT(HsmTst.d11)
            return 0
        elif e.sig == A_SIG:
            self._add_message("d1-A;")
            self.TRAN(HsmTst.d1)
            return 0
        elif e.sig == B_SIG:
            self._add_message("d1-B;")
            self.TRAN(HsmTst.d11)
            return 0
        elif e.sig == C_SIG:
            self._add_message("d1-C;")
            self.TRAN(HsmTst.d2)
            return 0
        elif e.sig == D_SIG:
            if (not self.foo_):
                self._add_message("d1-D;")
                self.foo_ = 1
                self.TRAN(HsmTst.d)
                return 0
        elif e.sig == F_SIG:
            self._add_message("d1-F;")
            self.TRAN(HsmTst.d211)
            return 0
        elif e.sig == I_SIG:
            self._add_message("d1-I;")
            return 0
        return HsmTst.d

    def d11(self, e):
        """d11 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("d11-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("d11-EXIT;")
            return 0
        elif e.sig == D_SIG:
            if (self.foo_):
                self._add_message("d11-D;")
                self.foo_ = 0
                self.TRAN(HsmTst.d1)
                return 0
        elif e.sig == G_SIG:
            self._add_message("d11-G;")
            self.TRAN(HsmTst.d211)
            return 0
        elif e.sig == H_SIG:
            self._add_message("d11-H;")
            self.TRAN(HsmTst.d)
            return 0
        elif e.sig == TERMINATE_SIG:
            sys.exit()
            return 0
        return HsmTst.d1

    def d2(self, e):
        """d2 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("d2-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("d2-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("d2-INIT;")
            self.INIT(HsmTst.d211)
            return 0
        elif e.sig == F_SIG:
            self._add_message("d2-F;")
            self.TRAN(HsmTst.d11)
            return 0
        elif e.sig == I_SIG:
            if (not self.foo_):
                self._add_message("d2-I;")
                self.foo_ = 1
                return 0
        return HsmTst.d

    def d21(self, e):
        """d21 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("d21-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("d21-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("d21-INIT;")
            self.INIT(HsmTst.d211)
            return 0
        elif e.sig == A_SIG:
            self._add_message("d21-A;")
            self.TRAN(HsmTst.d21)
            return 0
        elif e.sig == B_SIG:
            self._add_message("d21-B;")
            self.TRAN(HsmTst.d211)
            return 0
        elif e.sig == G_SIG:
            self._add_message("d21-G;")
            self.TRAN(HsmTst.d1)
            return 0
        return HsmTst.d2

    def d211(self, e):
        """d211 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("d211-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("d211-EXIT;")
            return 0
        elif e.sig == D_SIG:
            self._add_message("d211-D;")
            self.TRAN(HsmTst.d21)
            return 0
        elif e.sig == H_SIG:
            self._add_message("d211-H;")
            self.TRAN(HsmTst.d)
            return 0
        return HsmTst.d21

    def s(self, e):
        """s state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("s-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("s-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("s-INIT;")
            self.INIT(HsmTst.s11)
            return 0
        elif e.sig == C_SIG:
            self._add_message("s-C;")
            self.TRAN(HsmTst.d)
            return 0
        elif e.sig == E_SIG:
            self._add_message("s-E;")
            self.TRAN(HsmTst.s11)
            return 0
        elif e.sig == I_SIG:
            if (self.foo_):
                self._add_message("s-I;")
                self.foo_ = 0
                return 0
        elif e.sig == TERMINATE_SIG:
            #sys.exit()
            return 0
        return qp.Hsm.top

    def s1(self, e):
        """s1 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("s1-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("s1-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("s1-INIT;")
            self.INIT(HsmTst.s11)
            return 0
        elif e.sig == A_SIG:
            self._add_message("s1-A;")
            self.TRAN(HsmTst.s1)
            return 0
        elif e.sig == B_SIG:
            self._add_message("s1-B;")
            self.TRAN(HsmTst.s11)
            return 0
        elif e.sig == C_SIG:
            self._add_message("s1-C;")
            self.TRAN(HsmTst.s2)
            return 0
        elif e.sig == D_SIG:
            if (not self.foo_):
                self._add_message("s1-D;")
                self.foo_ = 1
                self.TRAN(HsmTst.s)
                return 0
        elif e.sig == F_SIG:
            self._add_message("s1-F;")
            self.TRAN(HsmTst.s211)
            return 0
        elif e.sig == I_SIG:
            self._add_message("s1-I;")
            return 0
        return HsmTst.s

    def s11(self, e):
        """s11 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("s11-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("s11-EXIT;")
            return 0
        elif e.sig == D_SIG:
            if (self.foo_):
                self._add_message("s11-D;")
                self.foo_ = 0
                self.TRAN(HsmTst.s1)
                return 0
        elif e.sig == G_SIG:
            self._add_message("s11-G;")
            self.TRAN(HsmTst.s211)
            return 0
        elif e.sig == H_SIG:
            self._add_message("s11-H;")
            self.TRAN(HsmTst.s)
            return 0
        return HsmTst.s1

    def s2(self, e):
        """s2 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("s2-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("s2-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("s2-INIT;")
            self.INIT(HsmTst.s211)
            return 0
        elif e.sig == F_SIG:
            self._add_message("s2-F;")
            self.TRAN(HsmTst.s11)
            return 0
        elif e.sig == I_SIG:
            if (not self.foo_):
                self._add_message("s2-I;")
                self.foo_ = 1
                return 0
        return HsmTst.s

    def s21(self, e):
        """s21 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("s21-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("s21-EXIT;")
            return 0
        elif e.sig == qp.INIT_SIG:
            self._add_message("s21-INIT;")
            self.INIT(HsmTst.s211)
            return 0
        elif e.sig == A_SIG:
            self._add_message("s21-A;")
            self.TRAN(HsmTst.s21)
            return 0
        elif e.sig == B_SIG:
            self._add_message("s21-B;")
            self.TRAN(HsmTst.s211)
            return 0
        elif e.sig == G_SIG:
            self._add_message("s21-G;")
            self.TRAN(HsmTst.s1)
            return 0
        return HsmTst.s2

    def s211(self, e):
        """s211 state handler"""
        if e.sig == qp.ENTRY_SIG:
            self._add_message("s211-ENTRY;")
            return 0
        elif e.sig == qp.EXIT_SIG:
            self._add_message("s211-EXIT;")
            return 0
        elif e.sig == D_SIG:
            self._add_message("s211-D;")
            self.TRAN(HsmTst.s21)
            return 0
        elif e.sig == H_SIG:
            self._add_message("s211-H;")
            self.TRAN(HsmTst.s2)
            return 0
        return HsmTst.s21

    def dispatch(self, e):
        """Dispatch event to state machine"""
        if (e.sig < TERMINATE_SIG):
            self._add_message("\n" + \
                             (string.ascii_uppercase[e.sig - A_SIG]) + ":")
        qp.Hsm.dispatch(self, e)

    def _add_message(self, message):
        """Add message string to result"""
        self.result = self.result + message


class TestQHsm(unittest.TestCase):

    def test_transition_from_d211_to_d11(self):
        qhsm = HsmTst()
        qhsm.init()    # Initial transition
        qhsm.dispatch(qp.Event(E_SIG))
        self.assertTrue(qhsm.is_in(HsmTst.d11))

    def test_that_transitions_matches_expected_route(self):
        qhsm = HsmTst()
        qhsm.init()    # Initial transition
        qhsm.dispatch(qp.Event(A_SIG))
        qhsm.dispatch(qp.Event(B_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(E_SIG))
        qhsm.dispatch(qp.Event(I_SIG))
        qhsm.dispatch(qp.Event(F_SIG))
        qhsm.dispatch(qp.Event(I_SIG))
        qhsm.dispatch(qp.Event(I_SIG))
        qhsm.dispatch(qp.Event(F_SIG))
        qhsm.dispatch(qp.Event(A_SIG))
        qhsm.dispatch(qp.Event(B_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(E_SIG))
        qhsm.dispatch(qp.Event(G_SIG))
        qhsm.dispatch(qp.Event(H_SIG))
        qhsm.dispatch(qp.Event(H_SIG))
        qhsm.dispatch(qp.Event(C_SIG))
        qhsm.dispatch(qp.Event(G_SIG))
        qhsm.dispatch(qp.Event(C_SIG))
        qhsm.dispatch(qp.Event(C_SIG))

        # static transitions
        qhsm.dispatch(qp.Event(C_SIG))
        qhsm.dispatch(qp.Event(A_SIG))
        qhsm.dispatch(qp.Event(A_SIG))
        qhsm.dispatch(qp.Event(B_SIG))
        qhsm.dispatch(qp.Event(B_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(E_SIG))
        qhsm.dispatch(qp.Event(I_SIG))
        qhsm.dispatch(qp.Event(F_SIG))
        qhsm.dispatch(qp.Event(I_SIG))
        qhsm.dispatch(qp.Event(I_SIG))
        qhsm.dispatch(qp.Event(F_SIG))
        qhsm.dispatch(qp.Event(A_SIG))
        qhsm.dispatch(qp.Event(A_SIG))
        qhsm.dispatch(qp.Event(B_SIG))
        qhsm.dispatch(qp.Event(B_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(D_SIG))
        qhsm.dispatch(qp.Event(E_SIG))
        qhsm.dispatch(qp.Event(G_SIG))
        qhsm.dispatch(qp.Event(H_SIG))
        qhsm.dispatch(qp.Event(G_SIG))
        qhsm.dispatch(qp.Event(H_SIG))
        qhsm.dispatch(qp.Event(F_SIG))
        qhsm.dispatch(qp.Event(H_SIG))
        qhsm.dispatch(qp.Event(F_SIG))
        qhsm.dispatch(qp.Event(C_SIG))
        qhsm.dispatch(qp.Event(G_SIG))
        qhsm.dispatch(qp.Event(G_SIG))

        qhsm.dispatch(qp.Event(TERMINATE_SIG))
        # Check difference
        self.assertEqual(EXPECTED_STRING, qhsm.result)


if __name__ == '__main__':
    unittest.main()
