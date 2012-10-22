#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import unittest

from ropemode.decorators import Logger


class LoggerTests(unittest.TestCase):
    def test_Logger_called_with_no_args_doesnt_raise_TypeError(self):
        """
        When not initialized with a message display method, Logger
        prints the message to stdout without raising an exception.
        """
        logger = Logger()
        try:
            logger("a message")
        except TypeError:
            self.fail("logger raised TypeError unexpectedly")
