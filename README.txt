difflame

Copyright 2017 Edmundo Carmona Antoranz
Released under the terms of GPLv2

Show the output of diff with the additional information of blame.

Lines that remain the same or that were added will indicate when those lines were 'added' to the file
Lines that were removed will display the last revision where those lines were _present_ on the file (as provided by blame --reverse)

You can provide one or two branches. If you provide only one branch, HEAD will be assumed to be the second branch.

You can also provide paths (which will be proxied into git diff) after --.
