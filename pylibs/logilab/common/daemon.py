# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""A daemonize function (for Unices) and daemon mix-in class"""

__docformat__ = "restructuredtext en"

import os
import errno
import signal
import sys
import time
import warnings


def daemonize(pidfile=None, uid=None, umask=077):
    """daemonize a Unix process. Set paranoid umask by default.

    Return 1 in the original process, 2 in the first fork, and None for the
    second fork (eg daemon process).
    """
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    # XXX unix specific
    #
    # fork so the parent can exit
    if os.fork():   # launch child and...
        return 1
    # deconnect from tty and create a new session
    os.setsid()
    # fork again so the parent, (the session group leader), can exit.
    # as a non-session group leader, we can never regain a controlling
    # terminal.
    if os.fork():   # launch child again.
        return 2
    # move to the root to avoit mount pb
    os.chdir('/')
    # set umask if specified
    if umask is not None:
        os.umask(umask)
    # redirect standard descriptors
    null = os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)
    # filter warnings
    warnings.filterwarnings('ignore')
    # write pid in a file
    if pidfile:
        # ensure the directory where the pid-file should be set exists (for
        # instance /var/run/cubicweb may be deleted on computer restart)
        piddir = os.path.dirname(pidfile)
        if not os.path.exists(piddir):
            os.makedirs(piddir)
        f = file(pidfile, 'w')
        f.write(str(os.getpid()))
        f.close()
    # change process uid
    if uid:
        try:
            uid = int(uid)
        except ValueError:
            from pwd import getpwnam
            uid = getpwnam(uid).pw_uid
        os.setuid(uid)
    return None


class DaemonMixIn:
    """Mixin to make a daemon from watchers/queriers.
    """

    def __init__(self, configmod) :
        self.delay = configmod.DELAY
        self.name = str(self.__class__).split('.')[-1]
        self._pid_file = os.path.join('/tmp', '%s.pid'%self.name)
        if os.path.exists(self._pid_file):
            raise Exception('''Another instance of %s must be running.
If it i not the case, remove the file %s''' % (self.name, self._pid_file))
        self._alive = 1
        self._sleeping = 0
        self.config = configmod

    def _daemonize(self):
        if not self.config.NODETACH:
            if daemonize(self._pid_file) is None:
                # put signal handler
                signal.signal(signal.SIGTERM, self.signal_handler)
                signal.signal(signal.SIGHUP, self.signal_handler)
            else:
                return -1

    def run(self):
        """ optionally go in daemon mode and
        do what concrete class has to do and pauses for delay between runs
        If self.delay is negative, do a pause before starting
        """
        if self._daemonize() == -1:
            return
        if self.delay < 0:
            self.delay = -self.delay
            time.sleep(self.delay)
        while True:
            try:
                self._run()
            except Exception, ex:
                # display for info, sleep, and hope the problem will be solved
                # later.
                self.config.exception('Internal error: %s', ex)
            if not self._alive:
                break
            try:
                self._sleeping = 1
                time.sleep(self.delay)
                self._sleeping = 0
            except SystemExit:
                break
        self.config.info('%s instance exited', self.name)
        # remove pid file
        os.remove(self._pid_file)

    def signal_handler(self, sig_num, stack_frame):
        if sig_num == signal.SIGTERM:
            if self._sleeping:
                # we are sleeping so we can exit without fear
                self.config.debug('exit on SIGTERM')
                sys.exit(0)
            else:
                self.config.debug('exit on SIGTERM (on next turn)')
                self._alive = 0
        elif sig_num == signal.SIGHUP:
            self.config.info('reloading configuration on SIGHUP')
            reload(self.config)

    def _run(self):
        """should be overridden in the mixed class"""
        raise NotImplementedError()


import logging
from logilab.common.logging_ext import set_log_methods
set_log_methods(DaemonMixIn, logging.getLogger('lgc.daemon'))

## command line utilities ######################################################

L_OPTIONS = ["help", "log=", "delay=", 'no-detach']
S_OPTIONS = 'hl:d:n'

def print_help(modconfig):
    print """  --help or -h
    displays this message
  --log <log_level>
    log treshold (7 record everything, 0 record only emergency.)
    Defaults to %s
  --delay <delay>
    the number of seconds between two runs.
    Defaults to %s""" % (modconfig.LOG_TRESHOLD, modconfig.DELAY)

def handle_option(modconfig, opt_name, opt_value, help_meth):
    if opt_name in ('-h', '--help'):
        help_meth()
        sys.exit(0)
    elif opt_name in ('-l', '--log'):
        modconfig.LOG_TRESHOLD = int(opt_value)
    elif opt_name in ('-d', '--delay'):
        modconfig.DELAY = int(opt_value)
    elif opt_name in ('-n', '--no-detach'):
        modconfig.NODETACH = 1
