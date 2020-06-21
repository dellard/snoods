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
Helper class to manage setting the cursor to reflect
whether or not a Shift key is being pressed

There is a subtlety here: the Python tkinter events
for keystrokes distinguish between the left shift key
(Shift_L) and the right shift key (Shift_R), but the
Enter event only provides information about whether
either shift key is pressed.  This means that there's
several edge-cases that could occur, involving the
user moving the cursor in and out of the canvas (or
even switching the focus to another app) and pressing
and/or releasing both shift keys, and some of these
edge cases can't be distinguished.  The approach
taken by this code is to assume that this behavior is
rare and not worth worrying about: any shift keypress
turns the shift on, and any shift keyrelease turns it
it back off (so if you press both and release one,
then it's off).
"""


class SnoodsShiftCursor(object):
    """
    Set bindings for updating the cursor depending on
    whether the Shift key is being pressed
    """

    def __init__(
            self, canvas,
            up_cursor='pencil', down_cursor='dotbox'):

        self.canvas = canvas
        self.up_cursor = up_cursor
        self.down_cursor = down_cursor

        self.is_down = False
        self.install_bindings()
        self.canvas.focus_set()

    def make_shift_down(self):
        """
        Handle shift-pressed events
        """

        def callback(_event):
            """ callback for shift-pressed """
            self.is_down = True
            self.canvas.configure(cursor=self.down_cursor)

        return callback

    def make_shift_up(self):
        """
        Handle shift-released events
        """

        def callback(_event):
            """ callback for shift-released """
            self.is_down = False
            self.canvas.configure(cursor=self.up_cursor)

        return callback

    def make_enter(self):
        """
        Handle the entrance of the cursor to the canvas;
        detect whether the shift key is pressed when the
        cursor enters
        """

        def callback(event):
            """ callback for canvas-enter events """

            # NOTE: I can't find where the event state codes are
            # documented, but the low bit on the state value
            # seems to indicate whether the shift key is pressed
            #
            if event.state & 0x1:
                self.is_down = True
                self.canvas.configure(cursor=self.down_cursor)
            else:
                self.is_down = False
                self.canvas.configure(cursor=self.up_cursor)

            self.canvas.focus_set()

        return callback

    def install_bindings(self):
        """
        Set all the bindings for the shift-press, shift-release,
        and Enter events
        """

        self.canvas.bind('<KeyPress-Shift_L>', self.make_shift_down())
        self.canvas.bind('<KeyPress-Shift_R>', self.make_shift_down())
        self.canvas.bind('<KeyRelease-Shift_L>', self.make_shift_up())
        self.canvas.bind('<KeyRelease-Shift_R>', self.make_shift_up())
        self.canvas.bind('<Enter>', self.make_enter())
