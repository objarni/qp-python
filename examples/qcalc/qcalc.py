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

"""Python GTK port of the Quantum Calculator example

Debian package dependencies:
python-glade2
python-gtk2
"""

# Standard
import sys
import os.path
sys.path.insert(0, os.path.join('..', '..'))
                                # Expects us to be two levels below the library
import logging
import unittest

# External
import gtk
import gtk.glade

# Local
import qp

# System wide signal definitions
C_SIG, \
CE_SIG, \
DIGIT_0_SIG, \
DIGIT_1_9_SIG, \
POINT_SIG, \
OPER_SIG, \
EQUALS_SIG, \
TERMINATE_SIG, \
IGNORE_SIG = range(qp.USER_SIG, qp.USER_SIG + 9)

KEY_UNKNOWN = '?'
KEY_PLUS = '+'
KEY_MINUS = '-'
KEY_MULT = '*'
KEY_DIVIDE = '/'

# Setup logging
if sys.version_info[:2] < (2, 5):  # funcName variable not supported
    logging_format = "%(levelname)s %(name)s: %(message)s"
else:
    logging_format = "%(levelname)s %(name)s.%(funcName)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=logging_format)


class QCalcGui(object):
    """GTK GUI"""

    logger = logging.getLogger('QCalcGui')

    def __init__(self, engine):
        self.engine = engine  # Calculator engine
        self.engine.init()
        # Instantiate gui from glade file
        self.widgets = gtk.glade.XML('qcalc.glade')
        # Connect widget and handlers
        signals = {
            'button_0': (DIGIT_0_SIG, '0'),
            'button_1': (DIGIT_1_9_SIG, '1'),
            'button_2': (DIGIT_1_9_SIG, '2'),
            'button_3': (DIGIT_1_9_SIG, '3'),
            'button_4': (DIGIT_1_9_SIG, '4'),
            'button_5': (DIGIT_1_9_SIG, '5'),
            'button_6': (DIGIT_1_9_SIG, '6'),
            'button_7': (DIGIT_1_9_SIG, '7'),
            'button_8': (DIGIT_1_9_SIG, '8'),
            'button_9': (DIGIT_1_9_SIG, '9'),
            'button_c': (C_SIG, None),
            'button_ce': (CE_SIG, None),
            'button_point': (POINT_SIG, '.'),
            'button_plus': (OPER_SIG, KEY_PLUS),
            'button_minus': (OPER_SIG, KEY_MINUS),
            'button_divide': (OPER_SIG, KEY_DIVIDE),
            'button_mult': (OPER_SIG, KEY_MULT),
            'button_equals': (EQUALS_SIG, None),
        }
        for name, (sig, key) in signals.iteritems():
            widget = self.widgets.get_widget(name)
            widget.connect('clicked', self.button_clicked, sig, key)
        top = self.widgets.get_widget('top')
        top.connect('destroy', gtk.main_quit)
        top.show_all()

    def button_clicked(self, button, sig, key):
        # Main driver of state machine events
        # Create event from button signal handler
        e = qp.Event(sig)
        e.key = key
        self.engine.dispatch(e)
        text = self.engine.get_display()
        self.widgets.get_widget('display').set_label(text)


class QCalc(qp.Hsm):

    signals = [
        C_SIG,
        CE_SIG,
        DIGIT_0_SIG,
        DIGIT_1_9_SIG,
        POINT_SIG,
        OPER_SIG,
        EQUALS_SIG,
        TERMINATE_SIG,
        IGNORE_SIG,
    ]

    def __init__(self, disp_width=14):
        qp.Hsm.__init__(self, self.__class__.initial)
        self.logger = logging.getLogger('QCalc')
        self.disp_width = disp_width
        self.display_ = ' ' * self.disp_width
        self.operand1_ = 0
        self.operand2_ = 0
        self.op_key_ = KEY_UNKNOWN

    def initial(self, e):
        self.clear()
        self.INIT(self.__class__.on)

    def on(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.INIT_SIG:
            self.logger.info('init/')
            self.INIT(self.__class__.ready)
            return 0
        elif e.sig == C_SIG:
            self.clear()
            self.TRAN(self.__class__.on)
            return 0
        return qp.Hsm.top

    def ready(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.INIT_SIG:
            self.INIT(self.__class__.begin)
            return 0
        elif e.sig == DIGIT_0_SIG:
            self.clear()
            self.TRAN(self.__class__.zero1)
            return 0
        elif e.sig == DIGIT_1_9_SIG:
            self.clear()
            self.insert(e.key)
            self.TRAN(self.__class__.int1)
            return 0
        elif e.sig == POINT_SIG:
            self.clear()
            self.insert('0')
            self.insert('.')
            self.TRAN(self.__class__.frac1)
            return 0
        elif e.sig == OPER_SIG:
            self.operand1_ = eval(self.display_)
            self.op_key_ = e.key
            self.TRAN(self.__class__.op_entered)
            return 0
        return self.__class__.on

    def result(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        return self.__class__.ready

    def begin(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == OPER_SIG:
            if e.key == KEY_MINUS:
                self.TRAN(self.__class__.negated1)
                return 0
        return self.__class__.ready

    def negated1(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            self.negate()
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == OPER_SIG:
            if e.key == KEY_MINUS:
                self.logger.warning('ignored')
                return 0
        elif e.sig == CE_SIG:
            self.clear()
            self.TRAN(self.__class__.begin)
            return 0
        elif e.sig == DIGIT_0_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.zero1)
            return 0
        elif e.sig == DIGIT_1_9_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.int1)
            return 0
        elif e.sig == POINT_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.frac1)
            return 0
        return self.__class__.on

    def operand1(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == CE_SIG:
            self.clear()
            self.TRAN(self.__class__.begin)
            return 0
        elif e.sig == OPER_SIG:
            self.operand1_ = eval(self.display_)
            self.op_key_ = e.key
            self.TRAN(self.__class__.op_entered)
            return 0
        return self.__class__.on

    def zero1(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == DIGIT_0_SIG:
            self.logger.warning('ignored')
            return 0
        elif e.sig == DIGIT_1_9_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.int1)
            return 0
        elif e.sig == POINT_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.frac1)
            return 0
        return self.__class__.operand1

    def int1(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig in [DIGIT_0_SIG, DIGIT_1_9_SIG]:
            self.insert(e.key)
            return 0
        elif e.sig == POINT_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.frac1)
            return 0
        return self.__class__.operand1

    def frac1(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig in [DIGIT_0_SIG, DIGIT_1_9_SIG]:
            self.insert(e.key)
            return 0
        elif e.sig == POINT_SIG:
            self.logger.warning('ignored')
            return 0
        return self.__class__.operand1

    def error(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        return self.__class__.on

    def op_entered(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == OPER_SIG:
            if e.key == KEY_MINUS:
                self.clear()
                self.TRAN(self.__class__.negated2)
                return 0
        elif e.sig == DIGIT_0_SIG:
            self.clear()
            self.TRAN(self.__class__.zero2)
            return 0
        elif e.sig == DIGIT_1_9_SIG:
            self.clear()
            self.insert(e.key)
            self.TRAN(self.__class__.int2)
            return 0
        elif e.sig == POINT_SIG:
            self.clear()
            self.insert('0')
            self.insert('.')
            self.TRAN(self.__class__.frac2)
            return 0
        return self.__class__.on

    def negated2(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            self.negate()
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == OPER_SIG:
            if e.key == KEY_MINUS:
                self.logger.warning('ignored')
                return 0
        elif e.sig == CE_SIG:
            self.TRAN(self.__class__.op_entered)
            return 0
        elif e.sig == DIGIT_0_SIG:
            self.TRAN(self.__class__.zero2)
            return 0
        elif e.sig == DIGIT_1_9_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.int2)
            return 0
        elif e.sig == POINT_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.frac2)
            return 0
        return self.__class__.on

    def operand2(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == CE_SIG:
            self.clear()
            self.TRAN(self.__class__.op_entered)
            return 0
        elif e.sig == OPER_SIG:
            self.operand2_ = eval(self.display_)
            if self.eval():
                self.operand1_ = eval(self.display_)
                self.op_key_ = e.key
                self.TRAN(self.__class__.op_entered)
            else:
                self.TRAN(self.__class__.error)
            return 0
        elif e.sig == EQUALS_SIG:
            self.operand2_ = eval(self.display_)
            if self.eval():
                self.TRAN(self.__class__.result)
            else:
                self.TRAN(self.__class__.error)
            return 0
        return self.__class__.on

    def zero2(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig == DIGIT_0_SIG:
            self.logger.warning('ignored')
            return 0
        elif e.sig == DIGIT_1_9_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.int2)
            return 0
        elif e.sig == POINT_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.frac2)
            return 0
        return self.__class__.operand2

    def int2(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig in [DIGIT_0_SIG, DIGIT_1_9_SIG]:
            self.insert(e.key)
            return 0
        elif e.sig == POINT_SIG:
            self.insert(e.key)
            self.TRAN(self.__class__.frac2)
            return 0
        return self.__class__.operand2

    def frac2(self, e):
        if e.sig == qp.ENTRY_SIG:
            self.logger.info('entry/')
            return 0
        elif e.sig == qp.EXIT_SIG:
            self.logger.info('exit/')
            return 0
        elif e.sig in [DIGIT_0_SIG, DIGIT_1_9_SIG]:
            self.insert(e.key)
            return 0
        elif e.sig == POINT_SIG:
            self.logger.warning('ignored')
            return 0
        return self.__class__.operand2

    # Non-state methods

    def clear(self):
        self.display_ = ' ' * (self.disp_width - 1) + '0'
        self.len_ = 0

    def insert(self, key):
        if self.len_ == 0:
            self.display_ = self.display_[0:-1] + key
            self.len_ += 1
        elif self.len_ < self.disp_width - 1:
            self.display_ = self.display_[1:] + key
            self.len_ += 1
        else:
            self.logger.warning('Overflow')

    def negate(self):
        self.clear()
        self.display_ = self.display_[0:-2] + '-' + self.display_[-1]

    def eval(self):
        ok = True
        result = 0
        if self.op_key_ == KEY_PLUS:
            result = self.operand1_ + self.operand2_
        elif self.op_key_ == KEY_MINUS:
            result = self.operand1_ - self.operand2_
        elif self.op_key_ == KEY_MULT:
            result = self.operand1_ * self.operand2_
        elif self.op_key_ == KEY_DIVIDE:
            if abs(self.operand2_) > 1e-10:
                result = float(self.operand1_) / float(self.operand2_)
            else:
                self.display_ = "Error 0"
                ok = False
        else:
            assert False
        if ok:
            if abs(result) < 1.0e10:
                self.display_ = '%14.11g' % result
            else:
                self.display_ = 'Error 1'
                ok = False
        return ok

    def get_display(self):
        return self.display_


class TestQCalc(unittest.TestCase):

    def setUp(self):
        self.dut = QCalc()
        self.dut.init()

    def test_that_clear_leaves_display_with_single_zero(self):
        # Given a QCalc engine with disp_width = 14
        self.dut.display_ = 'XXX'
        # When calling clear
        self.dut.clear()
        # Then
        self.assertEqual('             0', self.dut.display_)

    def test_that_clear_sets_len_to_zero(self):
        # Given a QCalc engine with disp_width = 14
        self.dut.len_ = 12
        # When calling clear
        self.dut.clear()
        # Then
        self.assertEqual(0, self.dut.len_)

    def test_that_insert_increases_len_when_two_less_than_disp_width(self):
        # Given a QCalc engine with disp_width = 12
        engine = QCalc(disp_width=12)
        engine.len_ = 10
        # When calling insert
        engine.insert('0')
        # Then
        self.assertEqual(11, engine.len_)

    def test_transition_from_begin_to_int1(self):
        # Given a QCalc engine in begin
        self.dut.TRAN(QCalc.begin)
        empty = qp.Event(qp.qep._QEP_EMPTY_SIG)
        self.dut.dispatch(empty)
        # When pressing a numeric button
        button = qp.Event(DIGIT_1_9_SIG)
        button.key = '1'
        self.dut.dispatch(button)
        # Then
        self.assertTrue(self.dut.is_in(QCalc.int1))

    def test_transition_from_int1_to_frac1(self):
        # Given a QCalc engine in int1
        self.dut.TRAN(QCalc.int1)
        empty = qp.Event(qp.qep._QEP_EMPTY_SIG)
        self.dut.dispatch(empty)
        # When pressing the point button
        button = qp.Event(POINT_SIG)
        button.key = '.'
        self.dut.dispatch(button)
        # Then
        self.assertTrue(self.dut.is_in(QCalc.frac1))


if __name__ == '__main__':
    engine = QCalc()
    app = QCalcGui(engine)
    gtk.main()
