#difflame

##Licensing
Copyright 2017 Edmundo Carmona Antoranz  
Released under the terms of GPLv2


##Keywords
git diff blame

##Description
Show the output of git diff with the additional information of git blame for
added/removed lines so that it's 'trivial' to find out who did what.

Example output (from difflame project itself, two revisions apart):
```
$ ./difflame.py c4dae4fdd8ba883 97d230ce523
diff --git a/difflame.py b/difflame.py
index ff65112..ec21fcd 100755
--- a/difflame.py
+++ b/difflame.py
@@ -51,7 +51,7 @@ REVISIONS_INFO_CACHE=dict()
 9d2e8d43 (Edmundo 2017-02-02 22:11:09 -0600  51) 
 18ecda88 (Edmundo 2017-02-15 00:42:18 -0600  52) '''
 cb526767 (Edmundo 2017-02-15 01:01:06 -0600  53) caches to save:
        cd789a5 removing an unnecessary TODO
-cd789a5 (Edmundo 2017-02-15 01:10:15 -0600 54)     - reverse blamed files # TODO consider cleaning this when we finish processing a file
+cd789a51 (Edmundo 2017-02-15 01:10:15 -0600  54)     - reverse blamed files
 cb526767 (Edmundo 2017-02-15 01:01:06 -0600  55)     - diff of files when analyzing revisions (merges and so on)
 cb526767 (Edmundo 2017-02-15 01:01:06 -0600  56) 
 18ecda88 (Edmundo 2017-02-15 00:42:18 -0600  57) BLAMED_FILES_CACHE[originating_revision][final_revision][filename] = lines
@@ -120,7 +120,7 @@ class DiffFileObject:
 d75f61ea (Edmundo 2017-02-11 16:28:58 -0600 120)             file_name = file_name[2:]
 d75f61ea (Edmundo 2017-02-11 16:28:58 -0600 121)         
 d75f61ea (Edmundo 2017-02-11 16:28:58 -0600 122)         # starting to build git command arguments
        97d230c Print filenames appropiately on deleted lines
-97d230c (Edmundo 2017-02-15 19:51:46 -0600 123)         git_blame_opts=["blame", "--no-progress"]
+97d230ce (Edmundo 2017-02-15 19:51:46 -0600 123)         git_blame_opts = []
 d75f61ea (Edmundo 2017-02-11 16:28:58 -0600 124)         
 d75f61ea (Edmundo 2017-02-11 16:28:58 -0600 125)         for hunk_position in hunk_positions:
```

##Output Format
Lines that remain the same or that were added will indicate when those lines
were *added* to the file.
Lines that were removed will display the revision where the line was removed.
When it's not possible to pinpoint the revision where it was deleted, the last
revision where that line was present is reported instead (as reported by
`git blame --reverse`). When this happens, a percentage sign (__%__) will be used as
the prefix of the deleted line (instead of the usual -).

Notice how a *'hint'* line is printed for lines that are removed/added and that
relate to the same revision. This is so that it's possible to get a little more
information about the revision itself without having to resort to an additional
call to git show.

You can provide one or two *treeishs*. If you provide only one, __HEAD__ will be
assumed to be the second treeish.

You can also provide paths (which will be proxied into `git diff`) after __--__.

Parameters can be sent to `git diff` by using option __--diff-param__ (or __-dp__), for
example: `--diff-param=--color` 
Multiple parameters are possible, each one having a separate __--diff-param/-dp__.
Most times, different options will change diff output and it will break difflame

Parameters can be sent to `git blame` by using option __--blame-param__ (or __-bp__), for
example: `--blame-param=-l` `-bp=-t`
Multiple parameters are possible, each one having a separate __--blame-param/-bp__:

##Options
__--color/--no-color__: output with/without color.
If user doesn't specify --color/--no-color options then output will use
color if process is connected to a terminal
        
__-w__: skip space changes (in both diff and blame)
    
__--no-hints__: when printing added/removed lines, do not provide the hint
(one-line summary of the revision) before the lines themselves.
If a number of added/removed lines belong to the same revision one
after the other, a single hint line would be printed before them.
It would have looked something like this with hints disabled (taken
from git project):
```
diff --git a/fast-import.c b/fast-import.c
index f561ba833..64fe602f0 100644
--- a/fast-import.c
+++ b/fast-import.c
@@ -2218,13 +2218,17 @@ static uintmax_t do_change_note_fanout(
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2218)              char *fullpath, unsigned int fullpath_len,
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2219)              unsigned char fanout)
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2220) {
-02d0457eb4 (Junio C Hamano 2017-01-10 15:24:26 -0800 2221)     struct tree_content *t = root->tree;
+405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2221)      struct tree_content *t;
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2222)      struct tree_entry *e, leaf;
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2223)      unsigned int i, tmp_hex_sha1_len, tmp_fullpath_len;
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2224)      uintmax_t num_notes = 0;
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2225)      unsigned char sha1[20];
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2226)      char realpath[60];
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2227) 
+405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2228)      if (!root->tree)
+405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2229)              load_tree(root);
+405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2230)      t = root->tree;
+405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2231) 
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2232)      for (i = 0; t && i < t->entry_count; i++) {
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2233)              e = t->entries[i];
 2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2234)              tmp_hex_sha1_len = hex_sha1_len + e->name->str_len;
```
__--git-debug__
print debug information about git on stderr:
- executed commands (with total execution time in miliseconds)
- total commands run
