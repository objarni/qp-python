# -*- coding: utf-8 -*-
# Copyright (C) 2011-2014 Autolabel AB. All Rights Reserved.
#
# Author: Henrik Bohre
#
"""Unittest helper for testing Hsm and Active objects"""

# Standard
import unittest

# External
import mock

# Local
import sys
import qp
import qif


class QpTester(object):
    """Base class for testing code using QP"""

    def setUp(self):
        # Mock qp.QF.publish
        self.saved_publish = qp.QF.publish
        qp.QF.publish = mock.Mock()
        # Mock qp.Active.postFIFO
        self.saved_qp_active_postFIFO = qp.Active.postFIFO
        qp.Active.postFIFO = mock.Mock()
        # Mock qp.Active.stop
        self.saved_qp_active_stop = qp.Active.stop
        qp.Active.stop = mock.Mock()

    def tearDown(self):
        # Restore mocked objects
        qp.Active.stop = self.saved_qp_active_stop
        qp.Active.postFIFO = self.saved_qp_active_postFIFO
        qp.QF.publish = self.saved_publish

    def assertPublished(self, sig, par):
        matcher = Matcher(self.event_compare, qif.Event(sig, par))
        found = False
        for call in qp.QF.publish.call_args_list:
            if call[0][0] == matcher:
                found = True
                break
        if not found:  # Print events
            for call in qp.QF.publish.call_args_list:
                e = call[0][0]
                try:
                    print "%s(%s)" % (qif.name(e.sig),
                            qif.name(e.sig, e.par))
                except:
                    print "%s" % qif.name(e.sig)
            try:
                print "Expected: %s(%s)" % (qif.name(sig), qif.name(sig, par))
            except:
                print "Expected: %s" % qif.name(sig)
        assert found, 'Event not published'

    def assertPublishedJson(self, method, params):
        par = {
            'method': method,
            'params': params,
        }
        self.assertPublished(qif.JSON_SIGNAL, par)

    def assertNotPublished(self, sig, par=None):
        try:
            self.assertPublished(sig, par)
        except AssertionError:
            return  # Got an expected assertion
        assert False, 'Signal unexpectedly published'

    def assertPublishedSignal(self, sig):
        matcher = Matcher(self.signal_compare, qif.Event(sig, None))
        found = False
        for call in qp.QF.publish.call_args_list:
            if call[0][0] == matcher:
                found = True
                break
        assert found, 'Signal not published'

    def getPublished(self, sig):
        pars = []
        matcher = Matcher(self.signal_compare, qif.Event(sig, None))
        for call in qp.QF.publish.call_args_list:
            if call[0][0] == matcher:
                pars.append(call[0][0])
        return pars

    def clearPublished(self):
        qp.QF.publish.call_args_list = []

    def signal_compare(self, x, y):
        """Returns true if sig is equal"""
        return x.sig == y.sig

    def event_compare(self, x, y):
        """Returns true if sig and par are equal"""
        return x.sig == y.sig and x.par == y.par

    def assertDictContainsSubset(self, expected, result):
        for k, v in expected.iteritems():
            self.assertEqual(result[k], v)


class HsmTester(QpTester):
    """Tester for QP Hsms"""

    def setUp(self):
        QpTester.setUp(self)
        self.dut.init()

    def assertIsIn(self, state):
        assert self.dut.isIn(state), 'In state %r' % self.dut.state_

    def dispatch(self, sig, par=None, src=0):
        if isinstance(sig, qp.Event):
            e = sig
            sig = e.sig
        else:
            e = qif.Event(sig, par)
        if src:
            e.src = src
        if sig >= qp.USER_SIG:
            assert sig in self.dut.signals, 'Not subscribed to signal'
        self.dut.dispatch(e)

    def dispatch_json(self, method, params={}):
        self.dispatch(qif.JSON_SIGNAL, {'method': method, 'params': params})

    def set_state(self, state):
        self.dut.TRAN(state)
        self.dispatch(qp.qep._QEP_EMPTY_SIG, None)


class Matcher(object):
    """Helper class for matching call arguments"""
    def __init__(self, compare, obj):
        self.compare = compare
        self.obj = obj

    def __eq__(self, other):
        return self.compare(self.obj, other)


class QpUnitTest(unittest.TestCase, QpTester):
    """Help class for writing unit tests using QP"""

    def setUp(self):
        QpTester.setUp(self)
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        QpTester.tearDown(self)


class HsmUnitTest(unittest.TestCase, HsmTester):
    """Help class for writing unit tests for Hsm or Active objects.
    The qp.QF.publish function is mocked and its usage can be asserted.
    """

    def setUp(self):
        import logging
        logging.info('hej')
        HsmTester.setUp(self)
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        HsmTester.tearDown(self)


