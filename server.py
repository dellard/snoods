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
Server class for the Snoods system

The server simply relays messages between clients,
including sending all message history to any new
clients when they join.

There is no error checking on the messages -- nor
does the server understand the protocol, beyond
knowing how to find message boundaries.
"""


import select
import socket
import threading

from protocol import SnoodsProtocol


class SnoodsServer(threading.Thread):
    """
    Thread that runs a Snoods server on a given socket address.
    """

    def __init__(self, sockaddr):

        threading.Thread.__init__(self)

        self.sockaddr = sockaddr

        self.lock = threading.RLock()
        self.all_clients = set()

        self.boardid2clients = dict()
        self.boardid2clients['default'] = set()
        self.sock2board = dict()

        # map from the client sockets to the buffers used
        # for partial messages.  We cannot assume that every
        # recv() gets a complete message -- or only one message!
        #
        self.client2buf = dict()

        self.msg_history = dict()

        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(sockaddr)
        self.listener.listen()

    def init_new_sock(self, new_sock, board_id):
        """
        Catch up a new sock with the history of messages
        """

        if board_id not in self.msg_history:
            self.msg_history[board_id] = list()

        for msg in self.msg_history[board_id]:
            new_sock.send(msg + SnoodsProtocol.recsep)

    def relay_msgs(self, board_id, msgs):
        """
        Send all the msgs to all of the current clients
        """

        all_clients = self.boardid2clients[board_id]

        for msg in msgs:
            for sock in all_clients:
                try:
                    # print('sending [%s]' % str(msg))
                    sock.send(msg + SnoodsProtocol.recsep)
                except BaseException:
                    pass

    def run(self):

        all_clients = self.all_clients
        # all_clients = self.boardid2client[board_id]

        while True:
            all_msgs = dict()

            r_in = list([self.listener]) + list(all_clients)
            w_in = list()
            x_in = list(all_clients)

            r_out, _w_out, x_out = select.select(r_in, w_in, x_in, 0.1)

            for sock in r_out:
                if sock == self.listener:
                    board_id = 'default'

                    new_sock, _conn_addr = self.listener.accept()
                    self.init_new_sock(new_sock, board_id)
                    self.boardid2clients[board_id].add(new_sock)
                    self.all_clients.add(new_sock)
                    self.sock2board[new_sock] = board_id
                    self.client2buf[new_sock] = b''
                else:
                    try:
                        recv_val = sock.recv(8192)
                    except ConnectionResetError as _exc:
                        recv_val = 0

                    if recv_val:
                        self.client2buf[sock] += recv_val
                        # print('BUF ' + self.client2buf[sock].decode('utf-8'))

                        msgs, remainder = SnoodsProtocol.split_buf(
                                self.client2buf[sock])

                        self.client2buf[sock] = remainder

                        board_id = self.sock2board[sock]
                        if board_id not in all_msgs:
                            all_msgs[board_id] = list()

                        for msg in msgs:
                            cmd = SnoodsProtocol.parse_msg(msg)
                            print('cmd is %s' % cmd['command'])
                            if cmd['command'] == '<join':
                                new_board_id = cmd['board_id']
                                print('board_id is %s' % new_board_id)
                                self.sock2board[sock] = new_board_id

                                if new_board_id not in self.boardid2clients:
                                    self.boardid2clients[new_board_id] = set()

                                self.boardid2clients[new_board_id].add(sock)
                            else:
                                all_msgs[board_id].append(msg)
                    else:
                        self.all_clients.remove(sock)
                        self.client2buf[sock] = b''

            for sock in x_out:
                print('client exceptional: ' + str(sock))

            for board_id in all_msgs:
                # relay all of the messages for this board
                # to all of the current clients of this board
                #
                self.relay_msgs(board_id, all_msgs[board_id])

                # append the new messages to the message history,
                # for the benefit of future clients
                #
                if board_id not in self.msg_history:
                    self.msg_history[board_id] = list()

                self.msg_history[board_id] += all_msgs[board_id]
