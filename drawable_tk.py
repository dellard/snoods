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
The UI for the Snoods client
"""

import tkinter as tk

from protocol import SnoodsProtocol
from shift import SnoodsShiftCursor


class Point(object):
    """
    Utility class to provide a mutable (x, y) point
    """

    def __init__(self, x_pos, y_pos):
        self.x_pos = x_pos
        self.y_pos = y_pos


class Stylus(object):
    """
    Utility class to provide a "freehand" drawing action
    """

    def __init__(self, drawable):
        self.drawable = drawable

        self.prev_x, self.prev_y = -1, -1
        self.color = self.drawable.active_color[0]
        self.color = self.drawable.active_lwidth
        self.points = None
        self.group_item = None
        self.lwidth = 0

    def activate(self):
        """
        Set the bindings to deal with "freehand drawing"
        actions: middle button down, motion, and middle
        button up
        """

        # TODO: need to record the old bindings,
        # so we can restore them when deactivating
        #
        self.drawable.canvas.bind(
                '<ButtonPress-2>', self.makedown())
        self.drawable.canvas.bind(
                '<B2-Motion>', self.makemove())
        self.drawable.canvas.bind(
                '<ButtonRelease-2>', self.makeup())

    def makedown(self):
        """ Return the callback for a mouse-2-down event """

        def callback(event):
            self.prev_x, self.prev_y = event.x, event.y
            self.color = self.drawable.active_color[0]
            self.lwidth = self.drawable.active_lwidth
            self.points = list()
            self.points.append((event.x, event.y))

        return callback

    def makemove(self):
        """ Return the callback for a mouse-2-motion event """

        def callback(event):
            item = self.drawable.canvas.create_line(
                    (self.prev_x, self.prev_y, event.x, event.y),
                    fill=self.color, width=self.lwidth)

            if not self.group_item:
                self.group_item = 'group-%d' % item

            self.drawable.canvas.itemconfig(
                    item, tags=('moveable', self.group_item))
            self.prev_x, self.prev_y = event.x, event.y
            self.points.append((event.x, event.y))

        return callback

    def makeup(self):
        """ Return the callback for the mouse-2-release event """

        def callback(_event):

            viob_id = SnoodsProtocol.create_viob_id()
            self.drawable.register_obj(self.group_item, viob_id)

            self.push_freehand(
                    viob_id, self.points, self.color, self.lwidth)
            self.group_item = None
            self.points = None
        return callback

    def push_freehand(self, viob_id, points, color, lwidth, remote=False):
        """
        Push a freehand drawing event to the remote,
        if there is one
        """

        points = [(p[0], self.drawable.flip_y(p[1])) for p in self.points]
        points_str = ' '.join(['%x,%x' % (p[0], p[1]) for p in points])

        if not remote and self.drawable.viobc:
            self.drawable.viobc.push_freehand(
                    viob_id, points_str, color, lwidth)

    def apply_newfre(self, viob_id, points_str, lwidth, color):
        """
        Apply a freehand drawing message received from the remote
        """

        if viob_id in self.drawable.viob_id2item:
            # we already have this viob; no need to create it
            return

        line_width = int(lwidth)

        points_list = points_str.split()
        points = list()
        for point_str in points_list:
            p_x, p_y = point_str.split(',')
            points.append((int(p_x, 16), self.drawable.flip_y(int(p_y, 16))))

        group_item = None

        for ind in range(len(points) - 1):
            point1 = points[ind]
            point2 = points[ind + 1]
            item = self.drawable.canvas.create_line(
                    point1[0], point1[1],
                    point2[0], point2[1],
                    fill=color, width=line_width)

            if not group_item:
                group_item = 'group-%d' % item
                self.drawable.register_obj(group_item, viob_id)

            self.drawable.canvas.itemconfig(
                    item, tags=('moveable', group_item))


class SnoodsDrawableTk(object):
    """
    Top-level of the Snoods client UI
    """

    BASE_COLORS = [
            ('black', 'white'),
            ('red', 'white'),
            ('blue', 'white'),
            ('coral', 'black'),
            ('darkgreen', 'white'),
            ('sienna', 'white'),
            ('purple', 'white'),
            ('yellow', 'black')
            ]

    BASE_LINE_SIZES = [
            ('small', 2),
            ('medium', 4),
            ('large', 6)
            ]

    FONT_FACES = [
            'Helvetica', 'Times', 'Courier'
            ]

    FONT_SIZES = [
            10, 12, 15, 18, 24, 28
            ]

    def __init__(self, viobc=None, client=None):

        self.viobc = viobc
        self.client = client

        self.item2viob_id = dict()
        self.viob_id2item = dict()

        self.font_face = self.FONT_FACES[0]
        self.font_size = self.FONT_SIZES[
                int((len(self.FONT_SIZES) - 1) / 2)]
        self.font_weight = 'normal'

        # this is lame; this gets reset later
        #
        self.line_width = 3

        self.win = tk.Tk()
        self.win.title('snoods')
        self.frame = tk.Frame(self.win)

        def exit_callback():

            if self.client:
                self.client.stop()

            self.win.destroy()

        exit_frame = tk.Frame(self.frame)
        exit_button = tk.Button(
                exit_frame, text='Exit', command=exit_callback)
        exit_button.pack(anchor=tk.W)
        exit_frame.pack(anchor=tk.W)

        # self.frame = tk.Frame()

        # TODO figure out how to dynamically resize

        self.canvas = tk.Canvas(
                self.frame, width=1200, height=900, background='white')
        self.canvas.pack(expand=1, fill=tk.BOTH)
        self.canvas.update()

        self.frame.pack(expand=1, fill=tk.BOTH)
        self.frame.update()

        # Not sure why the height is always off by 2: does it
        # count the pixel border as part of the height?
        # Is this something dependent on the window manager?
        #
        self.canvas_height = self.canvas.winfo_height()

        self.active_color = self.BASE_COLORS[0]
        self.dragging_item = -1

        self.drag_mouse_mode()
        self.color_mouse_mode()
        self.delete_mouse_mode()

        subframe = tk.Frame(self.frame)
        self.make_color_bar(parent_frame=subframe)
        self.make_font_control(parent_frame=subframe)
        subframe.pack(side=tk.LEFT, anchor=tk.N)

        subframe = tk.Frame(self.frame)
        self.make_text_entry(parent_frame=subframe)
        subframe.pack(side=tk.LEFT, anchor=tk.NW)

        self.frame.pack()

        self.stylus = Stylus(self)
        self.stylus.activate()

        SnoodsShiftCursor(self.canvas)

    def make_rect_button(self):
        """
        Not currently used

        Adds a button for creating new rectangles
        """

        frame = tk.Frame(
                self.frame, relief=tk.RAISED, borderwidth=1)

        def rect_command(self):
            def callback():
                viob_id = SnoodsProtocol.create_viob_id()
                self.create_rect(
                        10, 200, 110, 310, viob_id,
                        bg_color=self.active_color[0])
            return callback

        rect_button = tk.Button(
                frame, text='box', height=1, width=6,
                command=rect_command(self))

        rect_button.pack(side=tk.TOP)

        return frame

    def make_font_control(self, parent_frame=None):

        if not parent_frame:
            parent_frame = self.frame

        frame = tk.Frame(
                parent_frame, relief=tk.RAISED, borderwidth=1)

        def face_command(face):
            """ Create a callback to choose a font face """
            def callback():
                self.font_face = face
                new_font = (face, self.font_size, self.font_weight)
                text_example.itemconfig(
                        text_example_item, {'font': new_font})
            return callback

        def size_command(size):
            """ Create a callback to choose a font size """
            def callback():
                self.font_size = size
                new_font = (self.font_face, size, self.font_weight)
                text_example.itemconfig(
                        text_example_item, {'font': new_font})
            return callback

        face_frame = tk.Frame(
                parent_frame, relief=tk.RAISED, borderwidth=1)

        button_font = ('Courier', 12, 'bold')

        button = tk.Button(
                face_frame, text='Font: ', font=button_font)
        button.grid(row=0, column=0)

        index = 1
        for face in self.FONT_FACES:
            button = tk.Button(
                    face_frame, text=face,
                    command=face_command(face))
            button.grid(row=0, column=index)
            index += 1

        size_frame = tk.Frame(
                parent_frame, relief=tk.RAISED, borderwidth=1)

        button = tk.Button(
                size_frame, text='Size: ', font=button_font)
        button.grid(row=0, column=0)

        index = 1
        for size in self.FONT_SIZES:
            button = tk.Button(
                    size_frame, text=str(size),
                    command=size_command(size))
            button.grid(row=0, sticky=tk.SW, column=index)
            index += 1

        face_frame.pack(side=tk.TOP, anchor=tk.W)
        size_frame.pack(side=tk.TOP, anchor=tk.W)

        text_example = tk.Canvas(
                frame, height=40, width=300)
        text_example_item = text_example.create_text(
                0, 40, text='Current Font',
                anchor=tk.SW, tag='label',
                font=(self.font_face, self.font_size, self.font_weight))

        text_example.pack(side=tk.TOP, anchor=tk.W)
        frame.pack(anchor=tk.W)

    def make_text_entry(self, parent_frame=None):
        """
        Create the widget for inserting a new text item
        and return the frame that contains it

        The text entry widget has an area for writing text,
        and a button for turning the text in the writing
        area into a new text item.
        """

        # FIXME: magic numbers define where the new text goes.
        #
        # TODO: it would be better to have appear closer to the
        # text entry box, so the user doesn't have to reach as
        # far to move it.
        #
        default_new_text_pos = (0, 0)

        if not parent_frame:
            parent_frame = self.frame

        frame = tk.Frame(
                parent_frame, relief=tk.RAISED, borderwidth=1)

        button_frame = tk.Frame(
                frame, relief=tk.RAISED, borderwidth=1)

        text_entry = tk.Text(
                frame, height=8, width=80,
                font=('Courier', 14, 'normal'))

        def text_command(self):
            """ Create the callback to insert text from the text entry area """

            def callback():
                text = text_entry.get(1.0, tk.END).strip()
                if text:
                    viob_id = SnoodsProtocol.create_viob_id()
                    self.create_text(
                            default_new_text_pos[0], default_new_text_pos[1],
                            text, viob_id,
                            self.active_color[0])
            return callback

        def clear_command(self):
            """ Create the callback to clear the text entry area """

            def callback():
                text_entry.delete(1.0, tk.END)
            return callback

        text_button = tk.Button(
                button_frame, text='Insert Text', height=1, width=12,
                command=text_command(self))

        clear_button = tk.Button(
                button_frame, text='Clear', height=1, width=12,
                command=clear_command(self))

        text_button.pack(side=tk.LEFT)
        clear_button.pack(side=tk.LEFT)
        button_frame.pack(side=tk.TOP, anchor=tk.W)
        text_entry.pack(side=tk.TOP)

        frame.pack(side=tk.TOP, anchor=tk.NW)

        return frame

    def make_color_bar(self, parent_frame=None):
        """
        Create the color bar for changing the active color,
        which is used as the color for new objects, or the
        color to use to repaint objects
        """

        if not parent_frame:
            parent_frame = self.frame

        frame = tk.Frame(
                parent_frame, relief=tk.RAISED, borderwidth=1)

        pallete = tk.Frame(frame)
        sizes = tk.Frame(frame)

        bg_col, fg_col = self.active_color
        active_button = tk.Button(
                sizes, text='Pen: ',
                height=1, width=11,
                font=('Courier', 12, 'bold'),
                anchor=tk.W,
                background=bg_col, activebackground=bg_col,
                foreground=fg_col, activeforeground=fg_col)
        active_button.grid(row=0, column=0)

        color_opts = SnoodsDrawableTk.BASE_COLORS
        size_opts = SnoodsDrawableTk.BASE_LINE_SIZES

        def color_command(self, bg_col, fg_col):
            def callback():
                self.active_color = (bg_col, fg_col)
                active_button.config(bg=bg_col, fg=fg_col)
            return callback

        def size_command(self, size, name):
            def callback():
                self.active_lwidth = size
                active_button.config(text='Pen: ' + name)
            return callback

        # Never use more than four columns,
        # no matter how many colors we have.
        #
        maxcols = 4

        row = 0
        column = 0
        for _i, color_opt in enumerate(color_opts, 1):
            bg_col, fg_col = color_opt

            button = tk.Button(
                    pallete, text='', height=1, width=8,
                    background=bg_col, activebackground=bg_col,
                    foreground=fg_col, activeforeground=fg_col,
                    command=color_command(self, bg_col, fg_col))
            button.grid(row=row, column=column)
            column += 1
            if column == maxcols:
                column = 0
                row += 1

        row = 0
        column = 1
        for _i, size_opt in enumerate(size_opts):
            name, size = size_opt

            button = tk.Button(
                    sizes, text=name, height=1, width=6,
                    command=size_command(self, size, name))
            button.grid(row=row, column=column)
            column += 1
            if column == maxcols:
                column = 0
                row += 1

        # Set the initial value to the first size,
        # whatever it happens to be
        #
        name, size = size_opts[0]
        size_command(self, size, name)()

        pallete.pack(anchor=tk.N)
        sizes.pack(side=tk.TOP, anchor=tk.W)

        frame.pack(side=tk.TOP, anchor=tk.W)

    def get_item_group(self, item):
        """
        Find the "group" of a grouped item.

        The convention is that items that are always treated
        as part of a group are given a tag of the form 'group-N'
        where N is the item number of one of the items in the
        group (typically the first one created).

        If the item is a grouped item, then just return the
        item.
        """

        item_group = item
        for tag in self.canvas.itemcget(item, 'tags').split():
            if tag.startswith('group-'):
                item_group = tag
                break

        return item_group

    def delete_mouse_mode(self):
        """
        Set up the "delete" mode for the mouse
        """

        def post_nuke(event):
            """ Callback when an item is chosen """

            item = self.canvas.find_closest(event.x, event.y)[0]
            item_group = self.get_item_group(item)

            if self.viobc:
                viob_id = self.item2viob_id[item_group]
                self.viobc.push_erase(viob_id)

        self.canvas.tag_bind(
                'moveable', '<Shift-ButtonPress-1>', post_nuke)

    def drag_mouse_mode(self):
        """
        Set the callbacks for 'dragging' or moving objects
        using the mouse
        """

        self.canvas.tag_bind(
                'moveable', '<ButtonPress-1>', self.drag_mouse_down)
        self.canvas.tag_bind(
                'moveable', '<ButtonRelease-1>', self.drag_mouse_release)

    def color_mouse_mode(self):
        """
        Set the callbacks for re-coloring objects using the mouse
        """

        self.canvas.tag_bind(
                'moveable', '<ButtonPress-3>', self.color_mouse_down)
        self.canvas.tag_bind(
                'moveable', '<ButtonRelease-3>', self.color_mouse_release)

    def register_obj(self, item, viob_id):
        """
        Associate a given viob_id and item

        Objects are referenced at the protocol level by viob_id,
        but locally, for tkinter, each object has an item identifier
        (which may be a group identifier for a grouped object)
        that must be used as the object name for Tk operations
        """

        # TODO: check that there's not already a mapping!
        self.viob_id2item[viob_id] = item
        self.item2viob_id[item] = viob_id

    def create_rect(
            self, ll_x, ll_y, ur_x, ur_y, viob_id,
            bg_color=None, remote=False):
        """
        Create a rectangle
        """

        if not bg_color:
            bg_color = self.active_color[0]

        item = self.canvas.create_rectangle(
                ll_x, self.flip_y(ll_y),
                ur_x, self.flip_y(ur_y),
                fill=bg_color, tag='moveable')
        self.register_obj(item, viob_id)

        if not remote and self.viobc:
            self.viobc.push_create_rect(
                    viob_id, ll_x, ll_y, ur_x, ur_y, bg_color)

        return item

    def create_text(
            self, ll_x, ll_y, text, viob_id,
            fg_color=None,
            font=None, size=None, weight=None,
            remote=False):
        """
        Platform-independent procedure to create a text object
        """

        if not fg_color:
            fg_color = self.active_color[1]

        if not font:
            font = self.font_face
        if not size:
            size = self.font_size
        if not weight:
            weight = self.font_weight

        font_des = (font, size, weight)
        item = self.create_text_widget(
                ll_x, self.flip_y(ll_y), text, fg_color, font_des)

        self.register_obj(item, viob_id)
        if not remote and self.viobc:
            self.viobc.push_create_text(
                    viob_id, ll_x, ll_y, text,
                    fg_color, font, size, weight)

        return item

    def create_text_widget(
            self, ll_x, ll_y, text, fill_color, font_des):
        """
        Platform-dependent procedure to create a text object

        This must return an indentifier for the new text object
        """

        return self.canvas.create_text(
                ll_x, ll_y, text=text,
                fill=fill_color, font=font_des,
                anchor=tk.SW, tag='moveable')

    def apply_join(self, command, board_id):
        """
        Join a whiteboard

        If there's anything on the default whiteboard (or any
        other previous whiteboard) then we need to erase it
        when we join a new whiteboard.  Otherwise our view
        may be inconsistent with other viewers.
        """

        self.canvas.delete('all')
        self.win.title('snoods - %s' % board_id)

    def apply_erase(self, command, viob_id):
        """
        Erase a viob_id
        """

        if viob_id not in self.viob_id2item:
            # TODO log the error
            return

        item = self.viob_id2item[viob_id]
        self.canvas.delete(item)

    def apply_colupd(self, command, viob_id, color):
        """
        Apply a color update
        """

        if viob_id not in self.viob_id2item:
            # TODO log the error
            return

        item = self.viob_id2item[viob_id]
        self.canvas.itemconfig(item, {'fill': color})

    def apply_posupd(self, command, viob_id, ll_x, ll_y, ur_x, ur_y):
        """
        Apply a position update
        """

        if viob_id not in self.viob_id2item:
            # TODO log the error
            return

        item = self.viob_id2item[viob_id]
        llx = int(ll_x)
        flip_lly = self.flip_y(int(ll_y))
        urx = int(ur_x)
        flip_ury = self.flip_y(int(ur_y))

        # How we move an item depends on what type
        # of item it is
        #
        item_type = self.canvas.type(item)
        if item_type == 'rectangle':
            self.canvas.coords(item, llx, flip_lly, urx, flip_ury)
        elif item_type == 'text':
            self.canvas.coords(item, llx, flip_lly)
        elif item_type == 'line':
            # lines are tricky because it's likely to be a group
            # of lines, rather than a single line.  So instead of
            # just changing the coordinates of the line, we need
            # to find the bounding box of the set of lines, and
            # then the delta between the current coordinates and
            # the desired coordinates, and then move all the lines
            # by that amount.

            # Note the funny-looking order, because the canvas
            # is "upside down" in our coordinate system
            #
            cllx, _cury, _curx, clly = self.canvas.bbox(item)
            self.canvas.move(item, llx - cllx, flip_lly - clly)

    def apply_newrec(
            self, command, viob_id, ll_x, ll_y, ur_x, ur_y, color):
        """
        Apply a new rectangle creation
        """

        if viob_id in self.viob_id2item:
            # TODO log the error
            return

        llx = int(ll_x)
        lly = int(ll_y)
        urx = int(ur_x)
        ury = int(ur_y)

        self.create_rect(
                llx, lly, urx, ury, viob_id,
                bg_color=color, remote=True)

    def apply_newtxt(
            self, command, viob_id, ll_x, ll_y, text,
            color, font, size, weight):
        """
        Apply a new text block creation
        """

        if viob_id in self.viob_id2item:
            # we already have this viob; no need to create it
            return

        llx = int(ll_x)
        lly = int(ll_y)

        self.create_text(
                llx, lly, text, viob_id,
                fg_color=color, font=font, size=size, weight=weight,
                remote=True)

    def apply_newfre(self, command, viob_id, point_str, lwidth, color):
        """
        Apply a new "freehand" drawing creating
        """

        if viob_id in self.viob_id2item:
            return
        self.stylus.apply_newfre(viob_id, point_str, lwidth, color)

    def color_mouse_down(self, event):
        """
        Callback when the user selects a color for an object

        Note: this callback doesn't check whether the object is
        already the given color (because this can create a race
        condition): it always pushes the color update, even
        it appears to do nothing
        """

        item = self.canvas.find_closest(event.x, event.y)[0]
        item_group = self.get_item_group(item)
        self.canvas.itemconfig(
                item_group, {'fill': self.active_color[0]})

        if self.viobc:
            self.viobc.push_color_update(
                    self.item2viob_id[item_group], self.active_color[0])

    def color_mouse_release(self, event):
        """
        Callback when the user releases the cursor after selecting
        a color

        Right now, this does nothing
        """

        pass

    def drag_mouse_down(self, event):
        """
        Callback for the movement-by-dragging action
        """

        item = self.canvas.find_closest(event.x, event.y)[0]
        item_type = self.canvas.type(item)

        if item_type in ['line', 'rectangle', 'text']:
            event.widget.bind(
                    '<Motion>',
                    self.make_obj_mover(self.canvas, item, event))
        else:
            print('mouse_down unhandled [%s]' % item_type)

    def drag_mouse_release(self, event):
        """
        Callback for the movement-by-dragging release action

        Note that like color_mouse_down, this pushes a movement
        action even if the net movement is zero (i.e. someone
        drags an object around the screen, and the returns it
        to the original position) in order to avoid a race condition
        if more than one user is dragging the object at the same
        time
        """

        event.widget.unbind('<Motion>')
        item = self.dragging_item
        self.dragging_item = -1

        if item == -1:
            return

        # depending on the type of the object, the extent of the
        # current bounding box is calculated differently, so when
        # we need to caclulate the new position, we need to fudge
        # the bounding box so that the result is exactly what we
        # use in our calculation
        #
        item_type = self.canvas.type(item)
        if item_type == 'rectangle':
            x_fudge, y_fudge = 1, 1
        elif item_type == 'text':
            x_fudge, y_fudge = 1, 0
        elif item_type == 'line':
            x_fudge, y_fudge = -1, -1
        else:
            x_fudge, y_fudge = 0, 0

        # NOTE: This looks mixed up, but it's because the tkinter
        # canvas coordinate system is upside-down and we want them
        # right side up.
        #
        ll_x, ur_y, ur_x, ll_y = self.canvas.bbox(item)

        # Add the fudge factors
        #
        ll_x += x_fudge
        ll_y = self.flip_y(ll_y - y_fudge)
        ur_x -= x_fudge
        ur_y = self.flip_y(ur_y + y_fudge)

        # print('item %s viob_id %s moved to %d %d %d %d' %
        #         ( str(item), self.item2viob_id[item],
        #             ll_x, ll_y, ur_x, ur_y))

        if self.viobc:
            self.viobc.push_position_update(
                    self.item2viob_id[item], ll_x, ll_y, ur_x, ur_y)
            pass

    def make_obj_mover(self, canvas, item, down_event):

        item_group = self.get_item_group(item)
        self.dragging_item = item_group
        prev = Point(down_event.x, down_event.y)

        def mover(event):
            event.widget.move(
                    item_group, event.x - prev.x_pos, event.y - prev.y_pos)
            prev.x_pos, prev.y_pos = event.x, event.y

        return mover

    def flip_y(self, y_pos):
        """
        Flip the coordinate system so that the lower-left of the canvas
        is 0,0, instead of the upper-left
        """

        return self.canvas_height - y_pos

    def main(self):
        """
        Start the Tkinter main loop

        Does not return until the UI is shut down
        """

        tk.mainloop()
