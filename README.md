# Installing and running snoods

## Prerequisites

You need to have python3 and python3-tk installed on the client
and server machines.

## Setting up the server

On the machine you want to use as your server, create a directory for
the software, and untar the tarball there.  In that directory, execute:

    ./snoods -S

You can also do things like specify a different listening port (using
-p) or a file containing a pre-baked bunch of drawings, but the default
behavior is often enough.

Note that the server only listens for local connections, or at least
that's the way it's supposed to work.  Access control to a snoods
blackboard is done according to who can access the machine the server
runs on.  This may be improved in the future, but right now, the
whiteboard is accessible to all users who can access a machine.

## Setting up the client

On the client, assuming it's a different machine than
the server host:  create a directory for the software, and untar the
tarball there.  Don't run anything yet...  Keep reading.

## Creating a tunnel from the client to the server

You typically don't want to the run the client on the same machine as
the server, however, unless you're just trying things out.  (you can run
the client on a remote machine -- but the interactive response time
would probably be sluggish)  So you want to create an ssh tunnel between
a port on your workstation and the machine hosting the server:

    ssh -L 6540:localhost:6540 $SERVERNAME

This opens an SSH connection to $SERVERNAME and tunnels port 6540 (the
default snoods port) to the same port on $SERVERNAME

## Running the client

To run the client:

    ./snoods

On the bottom of the screen, there's a palette of different colors.
Clicking one of them makes the corresponding color active.  New items
are created with the active color.  If you don't see the palette, this
means that your screen is smaller than snoods thinks.  This can be
changed in the code, but no other way right now.

The left mouse button is for dragging objects from one place to another.

The middle mouse button draws a freehand curve when held.

The right mouse button re-colors objects with the active color.

Pressing the shift key and clicking on an object with the left
mouse button deletes the object.

If you enter text into the text window at the bottom of the screen and
press the "Insert Text" button, a new text object, containing the next
in the text window, appears at the lower left of the whiteboard, and
then you can move it wherever you prefer.

Any changes you make will appear on every other client.

```
Copyright 2020 - Daniel Ellard <ellard@gmail.com>
See LICENSE.txt for the license.
```
