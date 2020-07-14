# snoods - a simple shared whiteboard app 

## Description

__snoods__ provides the functionality of a shared "whiteboard":
users on different computers can draw, write, and make other changes
to their virtual whiteboard, and those changes will appear immediately
on the whiteboards of everyone else attached to the same whiteboard.

__snoods__ provides some extensions to a real whiteboard: users can
move text or drawings after they've been placed on the whiteboard,
and they can change the colors of objects on the whiteboard.

## Installing and running snoods

### Prerequisites

You need to have python3 and python3-tk installed on the client
and server machines.

### Setting up the server

On the machine you want to use as your server, create a directory for
the software, and then either clone this repo into that directory,
or untar a release tarball there.  In that directory, execute:

    ./snoods -S

You can also do things like specify a different listening port (using
-p) or a file containing a pre-baked bunch of drawings, but the default
behavior is often enough.

Note that the server only listens for local connections.  Access control
to a snoods blackboard is done by controlling who can access the machine
the server runs on.  This may be improved in the future, but right now,
the snoods server is accessible to all users who can access the machine
on which the server runs.

### Setting up the client

On the client, assuming it's a different machine than
the server host:  create a directory for the software,
and clone the repo or untar a release tarball there.

See [the users guide](USERSGUIDE.md) for information on how
to use the __snoods__ client.

---
Copyright 2020 - Daniel Ellard <ellard@gmail.com>

See LICENSE.txt for license information.
