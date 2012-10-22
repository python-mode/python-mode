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


class LoggerMessageHandlerTests(unittest.TestCase):
    def setUp(self):
        self.message = ""
        self.logger = Logger()
        self.logger.message = self._echo

    def _echo(self, message):
        self.message += message

    def test_message_handler_with_no_short_message(self):
        """Test that message handler is called"""
        self.logger("a message")
        self.assertEqual(self.message, "a message")

    def test_only_short_True(self):
        """Test that only_short=True prints only the short message"""
        self.logger.only_short = True
        self.logger("a long message", "a short message")
        self.assertEqual(self.message, "a short message")

    def test_only_short_False(self):
        """Test that only_short=False prints both messages"""
        self.logger.only_short = False
        self.logger("a long message", "a short message")
        self.assertEqual(self.message, "a long messagea short message")
