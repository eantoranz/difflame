#!/usr/bin/python

# tool to see who introduced changes on files
# Copyright Edmundo Carmona Antoranz 2017
# Released under the terms of GPLv2

# for starters, will get 2 parameters: two treeishs to compare
# For lines added, will use normal blame operation of the file
# For lines removed, will use reverse blame operation

import subprocess
import sys

def run_git_command(args):
    """
    Run a git command. If there is an error, will throw an exception. Otherwise, output will be returned
    """
    command = ["git"]
    command.extend(args)
    return subprocess.check_output(command)

if len(sys.argv) < 3:
    # not enough parameters
    sys.stderr.write("Not enough parameters\n")
    sys.stderr.write("Need to provide at least 2 treeishs to work on\n")
    exit(1)

# got at least two parameters
# will probably have to go through all the parameters (when we have them) in order to parse them

# finally, will get the two branches where we will work on
treeish1=sys.argv[-2]
treeish2=sys.argv[-1]

try:
    print run_git_command(["diff", "--color", treeish1 + ".." + treeish2])
except Exception as e:
    print "there was an error running git"
    print e
