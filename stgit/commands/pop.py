# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from stgit import argparse
from stgit.argparse import opt
from stgit.commands import common
from stgit.lib import transaction

__copyright__ = """
Copyright (C) 2005, Catalin Marinas <catalin.marinas@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see http://www.gnu.org/licenses/.
"""

help = 'Pop one or more patches from the stack'
kind = 'stack'
usage = ['[options] [--] [<patch1>] [<patch2>] [<patch3>..<patch4>]']
description = """
Pop the topmost patch or a range of patches from the stack. The
command fails if there are conflicts or local changes (and --keep was
not specified).

A series of pop and push operations are performed so that only the
patches passed on the command line are popped from the stack. Some of
the push operations may fail because of conflicts ("stg undo" would
revert the last push operation)."""

args = [argparse.patch_range(argparse.applied_patches)]
options = [
    opt('-a', '--all', action = 'store_true',
        short = 'Pop all the applied patches'),
    opt('-s', '--spill', action = 'store_true',
        short = 'Pop a patch, keeping its modifications in the tree'),
    opt('-n', '--number', type = 'int',
        short = 'Pop the specified number of patches', long = '''
        Pop the specified number of patches.

        With a negative number, pop all but that many patches.'''),
    ] + argparse.keep_option()

directory = common.DirectoryHasRepositoryLib()

def func(parser, options, args):
    """Pop the given patches or the topmost one from the stack."""
    stack = directory.repository.current_stack
    iw = stack.repository.default_iw
    clean_iw = (not options.keep and not options.spill and iw) or None
    trans = transaction.StackTransaction(stack, 'pop',
                                         check_clean_iw = clean_iw)

    if options.number == 0:
        # explicitly allow this without any warning/error message
        return

    if not trans.applied:
        raise common.CmdException('No patches applied')

    if options.all:
        patches = trans.applied
    elif options.number is not None:
        # reverse it twice to also work with negative or bigger than
        # the length numbers
        patches = trans.applied[::-1][:options.number][::-1]
    elif not args:
        patches = [trans.applied[-1]]
    else:
        patches = common.parse_patches(args, trans.applied, ordered = True)

    if not patches:
		#FIXME: Why is this an error, and not just a noop ?
        raise common.CmdException('No patches to pop')

    if options.spill:
        if set(stack.patchorder.applied[-len(patches):]) != set(patches):
            parser.error('Can only spill topmost applied patches')
        iw = None # don't touch index+worktree

    applied = [p for p in trans.applied if p not in set(patches)]
    unapplied = patches + trans.unapplied
    try:
        trans.reorder_patches(applied, unapplied, iw = iw,
                              allow_interactive = True)
    except transaction.TransactionException:
        pass
    return trans.run(iw)
