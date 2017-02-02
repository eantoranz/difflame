difflame

Copyright 2017 Edmundo Carmona Antoranz
Released under the terms of GPLv2

Show the output of diff with the additional information of blame

Example output (from difflame project itself, two revisions apart, using blame
params to change default output from git blame):

$ difflame.py -bp=-t -bp=-e 3d426842 6e2bfb8f
diff --git a/difflame.py b/difflame.py
index f6e879b..e3a2b65 100755
--- a/difflame.py
+++ b/difflame.py
@@ -38,10 +38,10 @@ def get_blame_info_hunk(treeish, file_name, hunk_position, treeish2=None):
 73dcdd5d (<eantoranz@gmail.com> 1484713110 -0600 38)         starting_line*=-1
 f22b4b2b (<eantoranz@gmail.com> 1484711061 -0600 39)     ending_line=starting_line+int(hunk_position[1])-1
 73dcdd5d (<eantoranz@gmail.com> 1484713110 -0600 40)     if treeish2 == None:
-f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 41)         return run_git_command(["blame", "--quiet", "-L", str(starting_line) + "," + str(ending_line), treeish, "--", file_name])
+6e2bfb8f (<eantoranz@gmail.com> 1484715079 -0600 41)         return run_git_command(["blame", "--no-progress", "-L", str(starting_line) + "," + str(ending_line), treeish, "--", file_name])
 73dcdd5d (<eantoranz@gmail.com> 1484713110 -0600 42)     else:
 73dcdd5d (<eantoranz@gmail.com> 1484713110 -0600 43)         # reverse blame
-f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 44)         return run_git_command(["blame", "--quiet", "-L", str(starting_line) + "," + str(ending_line), "--reverse", treeish2 + ".." + treeish, "--", file_name])
+6e2bfb8f (<eantoranz@gmail.com> 1484715079 -0600 44)         return run_git_command(["blame", "--no-progress", "-L", str(starting_line) + "," + str(ending_line), "--reverse", treeish2 + ".." + treeish, "--", file_name])
 f22b4b2b (<eantoranz@gmail.com> 1484711061 -0600 45) 
 f22b4b2b (<eantoranz@gmail.com> 1484711061 -0600 46) def process_hunk_from_diff_output(output_lines, starting_line, original_name, final_name, treeish1, treeish2):
 e621c863 (<eantoranz@gmail.com> 1484708773 -0600 47)     """
@@ -112,16 +112,20 @@ def process_file_from_diff_output(output_lines, starting_line):
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 112)     diff_line = output_lines[i].split()
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 113)     if diff_line[0] != "diff":
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 114)         raise Exception("Doesn't seem to exist a 'diff' line at line " + str(i + 1) + ": " + output_lines[i])
-^3d42684 (<eantoranz@gmail.com> 1484713578 -0600 115)     original_name = diff_line[1]
-^3d42684 (<eantoranz@gmail.com> 1484713578 -0600 116)     final_name = diff_line[2]
+f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 115)     original_name = diff_line[2]
+f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 116)     final_name = diff_line[3]
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 117)     print output_lines[i]; i+=1
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 118)     
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 119)     # let's get to the line that starts with ---
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 120)     while i < len(output_lines) and not output_lines[i].startswith("---"):
+f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 121)         if output_lines[i].startswith("diff"):
+6e2bfb8f (<eantoranz@gmail.com> 1484715079 -0600 122)             # just finished a file without content changes
+f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 123)             return i
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 124)         print output_lines[i]; i+=1
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 125)     
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 126)     if i >= len(output_lines):
-^3d42684 (<eantoranz@gmail.com> 1484713578 -0600 124)         raise Exception("Couln't find line starting with --- for a file (" + original_name + ", " + final_name + ")")
+f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 127)         # a file without content was the last on the patch
+f135bf04 (<eantoranz@gmail.com> 1484715050 -0600 128)         return i
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 129)     
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 130)     print output_lines[i]; i+=1 # line with ---
 c661286f (<eantoranz@gmail.com> 1484705407 -0600 131)     



Lines that remain the same or that were added will indicate when those lines
were 'added' to the file.
Lines that were removed will display the last revision where those lines were
_present_ on the file (as provided by git blame --reverse).

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
        
    -w: skip space changes (both in diff and blame)
    
    --hints: when printing added lines, provide the hint (one-line summary of the revision)
        before the lines themselves.
        if a number of added lines belong to the same revision one after the other, a single
        hint line will be printed before them.
        It would look something like this (taken from git project):
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
