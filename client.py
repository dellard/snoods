# Copyright 2020 - Daniel Ellard <ellard@gmail.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Basic client for the Snoods protocol

Almost all of the actual "work" is done elsewhere;
this is just a basic client that responds to messages
from the server
"""

import socket
import threading
import time

from protocol import SnoodsProtocol
from drawable_tk import SnoodsDrawableTk


class SnoodsClient(threading.Thread):
    """
    Create a basic client, with a drawable UI
    """

    def __init__(self, sockaddr, board_id=None):
        threading.Thread.__init__(self)

        sock = socket.socket()
        sock.connect(sockaddr)
        sock.settimeout(0.05)

        self.wire = SnoodsProtocol(sock)

        if board_id:
            self.wire.push_join(board_id)

        self.drawable = SnoodsDrawableTk(
                viobc=self.wire, client=self)
        self.do_run = True

        # At some point later, you need to start the UI, via:
        # self.drawable.main()
        # but this *must* be after this thread is started!

    def stop(self):
        """ Mark this thread as stopped """

        self.do_run = False

    def apply_msg(self, msg):
        """
        When a message arrives from the server, apply it
        to update an existing object or create a new one
        """

        # print('new msg %s' % str(msg))

        cmd = msg['command']

        if cmd == '<colupd':
            self.drawable.apply_colupd(**msg)
        elif cmd == '<posupd':
            self.drawable.apply_posupd(**msg)
        elif cmd == '<newrec':
            self.drawable.apply_newrec(**msg)
        elif cmd == '<newtxt':
            self.drawable.apply_newtxt(**msg)
        elif cmd == '<newfre':
            self.drawable.apply_newfre(**msg)
        elif cmd == '<erase':
            self.drawable.apply_erase(**msg)

    def run(self):

        while self.do_run:
            time.sleep(0.02)
            msgs = self.wire.recv_msgs()
            for msg in msgs:
                cmd = self.wire.parse_msg(msg)
                if cmd:
                    self.apply_msg(cmd)
