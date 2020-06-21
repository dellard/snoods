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


import socket
import uuid


class SnoodsProtocol(object):
    """
    Super simple wire/storage protocol for pushing/pulling changes

    This is just for prototyping; there's not much error checking
    here and bogus data can break everything

    TODO/FIXME: we MUST encode/decode the color names and texts
    so that they don't contain any <, newline, or / characters.
    """

    recsep = b'\n'

    """
    A map from "special" characters to their escaped form
    """
    char2esc = {
            '<': '&lt;',
            '>': '&gt;',
            '\n': '&nl;',
            '\t': '&tab;',
            '/': '&fs;',
            # '&' must be last (for unescape_str) because
            # it is the prefix for all the escaped forms
            '&': '&amp;'
            }

    def __init__(self, sock):
        self.sock = sock
        self.input_buf = b''

    @staticmethod
    def escape_str(text):
        """
        "Escape" the text by return a new string with each
        each special character in the text substituted with
        its expansion
        """

        return ''.join(
                SnoodsProtocol.char2esc.get(char, char) for char in text)

    @staticmethod
    def unescape_str(text):
        """
        "Unescape" the text by returning a new string which
        each instance, in the original text, of an expansion
        replaced with the original, unescaped character
        """

        for char, e_echar in SnoodsProtocol.char2esc.items():
            text = text.replace(e_echar, char)
        return text

    @staticmethod
    def split_buf(buf):
        """
        Split a byte string into messages, returning the array of
        messages and the left-over at the end of the buffer that
        is the incomplete prefix of the next message.

        This depends implicitly on the format of the messages,
        and right now the messages are encoded in super simple
        manner
        """

        pieces = buf.split(SnoodsProtocol.recsep)
        if len(pieces) == 1:
            return list(), pieces[0]
        else:
            return pieces[:-1], pieces[-1]

    @staticmethod
    def create_viob_id():
        return str(uuid.uuid4())

    @staticmethod
    def msgs_from_file(fname):

        with open(fname) as fin:
            msgs = fin.readlines()

        msgs_text = [msg.encode('utf-8') for msg in msgs]

        return msgs_text

    def recv_msgs(self):

        try:
            new_buf = self.sock.recv(8129)
        except socket.timeout as _exc:
            return list()
        # TODO: watch for other exceptions

        self.input_buf += new_buf

        msgs_text = list()
        msgs, self.input_buf = SnoodsProtocol.split_buf(self.input_buf)
        if msgs:
            msgs_text = [msg.strip() for msg in msgs]

            # print('msgs_text = %s' % str(msgs_text))

        return msgs_text

    def parse_msg(self, text):

        msg = dict()
        fields = [s.decode('utf-8') for s in text.split(b'/')]
        # print('text = %s' % str(text))
        # print('fields = %s' % str(fields))

        if fields[0] == '<colupd':
            msg['command'] = fields[0]
            msg['viob_id'] = fields[1]
            msg['color'] = fields[2]

        elif fields[0] == '<posupd':
            msg['command'] = fields[0]
            msg['viob_id'] = fields[1]
            msg['ll_x'] = fields[2]
            msg['ll_y'] = fields[3]
            msg['ur_x'] = fields[4]
            msg['ur_y'] = fields[5]

        elif fields[0] == '<newrec':
            msg['command'] = fields[0]
            msg['viob_id'] = fields[1]
            msg['ll_x'] = fields[2]
            msg['ll_y'] = fields[3]
            msg['ur_x'] = fields[4]
            msg['ur_y'] = fields[5]
            msg['color'] = SnoodsProtocol.unescape_str(fields[6])

        elif fields[0] == '<newtxt':
            msg['command'] = fields[0]
            msg['viob_id'] = fields[1]
            msg['ll_x'] = fields[2]
            msg['ll_y'] = fields[3]
            msg['text'] = SnoodsProtocol.unescape_str(fields[4])
            msg['color'] = SnoodsProtocol.unescape_str(fields[5])
            msg['font'] = SnoodsProtocol.unescape_str(fields[6])
            msg['size'] = SnoodsProtocol.unescape_str(fields[7])
            msg['weight'] = SnoodsProtocol.unescape_str(fields[8])

        elif fields[0] == '<newfre':
            msg['command'] = fields[0]
            msg['viob_id'] = fields[1]
            msg['color'] = SnoodsProtocol.unescape_str(fields[2])
            msg['lwidth'] = fields[3]
            msg['point_str'] = fields[4]

        elif fields[0] == '<erase':
            msg['command'] = fields[0]
            msg['viob_id'] = fields[1]

        # print(str(msg))
        return msg

    def push_erase(self, viob_id):
        e_viob_id = SnoodsProtocol.escape_str(str(viob_id))

        msg = '<erase/%s' % e_viob_id
        # print(msg)
        msg = msg.encode('utf-8')
        self.sock.send(msg + SnoodsProtocol.recsep)

    def push_color_update(self, viob_id, color):
        e_viob_id = SnoodsProtocol.escape_str(str(viob_id))
        e_color = SnoodsProtocol.escape_str(color)

        msg = '<colupd/%s/%s' % (e_viob_id, e_color)
        # print(msg)
        msg = msg.encode('utf-8')
        self.sock.send(msg + SnoodsProtocol.recsep)

    def push_position_update(self, viob_id, ll_x, ll_y, ur_x, ur_y):
        e_viob_id = SnoodsProtocol.escape_str(str(viob_id))

        msg = '<posupd/%s/%d/%d/%d/%d' % (
                e_viob_id, ll_x, ll_y, ur_x, ur_y)
        # print(msg)
        msg = msg.encode('utf-8')
        self.sock.send(msg + SnoodsProtocol.recsep)

    def push_create_rect(self, viob_id, ll_x, ll_y, ur_x, ur_y, bg_color):
        e_viob_id = SnoodsProtocol.escape_str(str(viob_id))
        e_bg_color = SnoodsProtocol.escape_str(bg_color)

        msg = '<newrec/%s/%d/%d/%d/%d/%s' % (
                e_viob_id, ll_x, ll_y, ur_x, ur_y, e_bg_color)
        # print(msg)
        msg = msg.encode('utf-8')
        self.sock.send(msg + SnoodsProtocol.recsep)

    def push_create_text(
            self, viob_id, ll_x, ll_y, text,
            fg_color, font, size, weight):
        e_viob_id = SnoodsProtocol.escape_str(str(viob_id))
        e_fg_color = SnoodsProtocol.escape_str(fg_color)
        e_font = SnoodsProtocol.escape_str(font)
        e_size = SnoodsProtocol.escape_str(str(size))
        e_weight = SnoodsProtocol.escape_str(weight)

        e_text = SnoodsProtocol.escape_str(text)

        msg = '<newtxt/%s/%d/%d/%s/%s/%s/%s/%s' % (
                e_viob_id, ll_x, ll_y, e_text,
                e_fg_color, e_font, e_size, e_weight)
        # print('SENDING = ' + msg)
        msg = msg.encode('utf-8')
        self.sock.send(msg + SnoodsProtocol.recsep)

    def push_freehand(self, viob_id, point_str, fg_color, lwidth):
        e_viob_id = SnoodsProtocol.escape_str(str(viob_id))
        e_fg_color = SnoodsProtocol.escape_str(fg_color)

        msg = '<newfre/%s/%s/%d/%s' % (
                e_viob_id, e_fg_color, lwidth, point_str)
        msg = msg.encode('utf-8')
        self.sock.send(msg + SnoodsProtocol.recsep)
