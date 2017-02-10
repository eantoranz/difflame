difflame

Copyright 2017 Edmundo Carmona Antoranz
Released under the terms of GPLv2

Show the output of diff with the additional information of blame

Example output (from difflame project itself, two revisions apart, using blame
params to change default output from git blame):

$ difflame.py -bp=-t 3d426842 6e2bfb8f
diff --git a/difflame.py b/difflame.py
index f6e879b..e3a2b65 100755
--- a/difflame.py
+++ b/difflame.py
@@ -38,10 +38,10 @@ def get_blame_info_hunk(treeish, file_name, hunk_position, treeish2=None):
 73dcdd5d (Edmundo 1484713110 -0600  38)         starting_line*=-1
 f22b4b2b (Edmundo 1484711061 -0600  39)     ending_line=starting_line+int(hunk_position[1])-1
 73dcdd5d (Edmundo 1484713110 -0600  40)     if treeish2 == None:
        6e2bfb8 use --no-progress on blame
-6e2bfb8 (Edmundo 2017-01-17 22:51:19 -060  41)         return run_git_command(["blame", "--quiet", "-L", str(starting_line) + "," + str(ending_line), treeish, "--", file_name])
+6e2bfb8f (Edmundo 1484715079 -0600  41)         return run_git_command(["blame", "--no-progress", "-L", str(starting_line) + "," + str(ending_line), treeish, "--", file_name])
 73dcdd5d (Edmundo 1484713110 -0600  42)     else:
 73dcdd5d (Edmundo 1484713110 -0600  43)         # reverse blame
        6e2bfb8 use --no-progress on blame
-6e2bfb8 (Edmundo 2017-01-17 22:51:19 -060  44)         return run_git_command(["blame", "--quiet", "-L", str(starting_line) + "," + str(ending_line), "--reverse", treeish2 + ".." + treeish, "--", file_name])
+6e2bfb8f (Edmundo 1484715079 -0600  44)         return run_git_command(["blame", "--no-progress", "-L", str(starting_line) + "," + str(ending_line), "--reverse", treeish2 + ".." + treeish, "--", file_name])
 f22b4b2b (Edmundo 1484711061 -0600  45) 
 f22b4b2b (Edmundo 1484711061 -0600  46) def process_hunk_from_diff_output(output_lines, starting_line, original_name, final_name, treeish1, treeish2):
 e621c863 (Edmundo 1484708773 -0600  47)     """
@@ -112,16 +112,20 @@ def process_file_from_diff_output(output_lines, starting_line):


OUTPUT FORMAT
Lines that remain the same or that were added will indicate when those lines
were 'added' to the file.
Lines that were removed will display the revision where the line was removed.
When it's not possible to pinpoint the revision where it was deleted, the last
revision where that line was present is reported instead (as reported by
git blame --reverse). When this happens, a percentage sign (%) will be used as
the prefix of the deleted line (instead of the usual -).

You can provide one or two treeishs. If you provide only one, HEAD will be
assumed to be the second treeish.

You can also provide paths (which will be proxied into git diff) after --.

Parameters can be sent to git diff by using option --diff-param (or -dp), for
example:
    --diff-param=--color
Multiple parameters are possible, each one having a separate --diff-param/-dp.
Most times, different options will change diff output and it will break difflame

Parameters can be sent to git blame by using option --blame-param (or -bp), for
example:
    --blame-param=-l
    -bp=-t
Multiple parameters are possible, each one having a separate --blame-param/-bp:
    --blame-param=-l -bp=-t

options:
    --color/--no-color: output with/without color
        if user doesn't specify --color/--no-color options then output will use
        color if process is connected to a terminal
        
    -w: skip space changes (in both diff and blame)
    
    --no-hints: when printing added lines, do not provide the hint (one-line summary of the revision)
        before the lines themselves.
        if a number of added lines belong to the same revision one after the other, a single
        hint line would be printed before them.
        It would have looked something like this with hints enabled (taken from git project):
            diff --git a/fast-import.c b/fast-import.c
            index f561ba833..64fe602f0 100644
            --- a/fast-import.c
            +++ b/fast-import.c
            @@ -2218,13 +2218,17 @@ static uintmax_t do_change_note_fanout(
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2218)              char *fullpath, unsigned int fullpath_len,
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2219)              unsigned char fanout)
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2220) {
            -02d0457eb4 (Junio C Hamano 2017-01-10 15:24:26 -0800 2221)     struct tree_content *t = root->tree;
                    405d7f4af fast-import: properly fanout notes when tree is imported
            +405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2221)      struct tree_content *t;
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2222)      struct tree_entry *e, leaf;
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2223)      unsigned int i, tmp_hex_sha1_len, tmp_fullpath_len;
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2224)      uintmax_t num_notes = 0;
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2225)      unsigned char sha1[20];
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2226)      char realpath[60];
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2227) 
                    405d7f4af fast-import: properly fanout notes when tree is imported
            +405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2228)      if (!root->tree)
            +405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2229)              load_tree(root);
            +405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2230)      t = root->tree;
            +405d7f4af6 (Mike Hommey   2016-12-21 06:04:48 +0900 2231) 
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2232)      for (i = 0; t && i < t->entry_count; i++) {
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2233)              e = t->entries[i];
             2a113aee9b (Johan Herland 2009-12-07 12:27:24 +0100 2234)              tmp_hex_sha1_len = hex_sha1_len + e->name->str_len;

    --git-debug
        print debug information about git on stderr:
            - executed commands
            - total commands run
