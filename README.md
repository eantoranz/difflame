# difflame

## Licensing
Copyright (c) 2017-2025 Edmundo Carmona Antoranz
Released under the terms of GPLv2


## Keywords
git diff blame

## Description
Show the output of git diff with the additional information of git blame for
added/removed lines so that it's 'trivial' to find out who did what.

## Output Format
Lines that remain the same or that were added will indicate when those lines
were *added* to the file.
Lines that were removed will display the commit where the line was removed.
When it's not possible to pinpoint the commit where it was deleted, the last
commit where that line was present is reported instead (as reported by
`git blame --reverse`). When this happens, a percentage sign (__%__) will be used as
the prefix of the deleted line (instead of the usual -).

Example output (from difflame project itself, two commits apart):
```
$ ./difflame c4dae4fdd8ba883 97d230ce523
diff --git a/difflame.py b/difflame.py
index ff65112..ec21fcd 100755
--- a/difflame.py
+++ b/difflame.py
@@ -51,7 +51,7 @@ REVISIONS_INFO_CACHE=dict()
 9d2e8d4 (Edmundo Carmona Antoranz 2017-02-02 22:11:09  51  51) 
 18ecda8 (Edmundo Carmona Antoranz 2017-02-15 00:42:18  52  52) '''
 cb52676 (Edmundo Carmona Antoranz 2017-02-15 01:01:06  53  53) caches to save:
        cd789a5: removing an unnecessary TODO
-cd789a5 (Edmundo Carmona Antoranz 2017-02-15 01:10:15  54    )     - reverse blamed files # TODO consider cleaning this when we finish processing a file
+cd789a5 (Edmundo Carmona Antoranz 2017-02-15 01:10:15      54)     - reverse blamed files
 cb52676 (Edmundo Carmona Antoranz 2017-02-15 01:01:06  55  55)     - diff of files when analyzing revisions (merges and so on)
 cb52676 (Edmundo Carmona Antoranz 2017-02-15 01:01:06  56  56) 
 18ecda8 (Edmundo Carmona Antoranz 2017-02-15 00:42:18  57  57) BLAMED_FILES_CACHE[originating_revision][final_revision][filename] = lines
@@ -120,7 +120,7 @@ class DiffFileObject:
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 120 120)             file_name = file_name[2:]
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 121 121)         
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 122 122)         # starting to build git command arguments
        97d230c: Print filenames appropiately on deleted lines
-97d230c (Edmundo Carmona Antoranz 2017-02-15 19:51:46 123    )         git_blame_opts=["blame", "--no-progress"]
+97d230c (Edmundo Carmona Antoranz 2017-02-15 19:51:46     123)         git_blame_opts = []
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 124 124)         
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 125 125)         for hunk_position in hunk_positions:
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 126 126)             hunk_position = hunk_position.split(',')
```

Notice how a *'hint'* line is printed for lines that are removed/added and that
relate to the same commit. This is so that it's possible to get a little more
information about the commit itself without having to resort to an additional
call to git show.

## Parameters
You can provide one or two *committishes*. If you provide only one, __HEAD__ will be
assumed to be the second committish.

You can also provide paths (which will be proxied into `git diff`) after __--__.

Parameters can be sent to `git diff` by using option __--diff-param__ (or __-dp__), for
example: `--diff-param=--color` 
Multiple parameters are possible, each one having a separate __--diff-param/-dp__.
Most times, different options will change diff output and it will break difflame

Parameters can be sent to `git blame` by using option __--blame-param__ (or __-bp__), for
example: `--blame-param=-l` `-bp=-t`
Multiple parameters are possible, each one having a separate __--blame-param/-bp__:

## Options
__--color/--no-color__: output with/without color.
If user doesn't specify --color/--no-color options then output will use
color if process is connected to a terminal

__-e__: show mail addresses of authors instead of their names.

__-s__: short output

__--progress/--no-progress__: progress is shown by default if running the process
on a tty. These options can be used to force showing/hiding it.
        
__-w__: skip space changes (in both diff and blame)
    
__--no-hints__: when printing added/removed lines, do not provide the hint
(one-line summary of the commit) before the lines themselves.
If a number of added/removed lines belong to the same commit one
after the other, a single hint line would be printed before them.
It would have looked something like this with hints disabled:
```
diff --git a/difflame.py b/difflame.py
index ff65112..ec21fcd 100755
--- a/difflame.py
+++ b/difflame.py
@@ -51,7 +51,7 @@ REVISIONS_INFO_CACHE=dict()
 9d2e8d4 (Edmundo Carmona Antoranz 2017-02-02 22:11:09  51  51) 
 18ecda8 (Edmundo Carmona Antoranz 2017-02-15 00:42:18  52  52) '''
 cb52676 (Edmundo Carmona Antoranz 2017-02-15 01:01:06  53  53) caches to save:
-cd789a5 (Edmundo Carmona Antoranz 2017-02-15 01:10:15  54    )     - reverse blamed files # TODO consider cleaning this when we finish processing a file
+cd789a5 (Edmundo Carmona Antoranz 2017-02-15 01:10:15      54)     - reverse blamed files
 cb52676 (Edmundo Carmona Antoranz 2017-02-15 01:01:06  55  55)     - diff of files when analyzing revisions (merges and so on)
 cb52676 (Edmundo Carmona Antoranz 2017-02-15 01:01:06  56  56) 
 18ecda8 (Edmundo Carmona Antoranz 2017-02-15 00:42:18  57  57) BLAMED_FILES_CACHE[originating_revision][final_revision][filename] = lines
@@ -120,7 +120,7 @@ class DiffFileObject:
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 120 120)             file_name = file_name[2:]
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 121 121)         
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 122 122)         # starting to build git command arguments
-97d230c (Edmundo Carmona Antoranz 2017-02-15 19:51:46 123    )         git_blame_opts=["blame", "--no-progress"]
+97d230c (Edmundo Carmona Antoranz 2017-02-15 19:51:46     123)         git_blame_opts = []
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 124 124)         
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 125 125)         for hunk_position in hunk_positions:
 d75f61e (Edmundo Carmona Antoranz 2017-02-11 16:28:58 126 126)             hunk_position = hunk_position.split(',')
```
__--git-debug__
print debug information about git on stderr:
- executed commands (with total execution time in miliseconds)
- total commands run
