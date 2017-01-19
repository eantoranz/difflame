#!/usr/bin/python

# tool to see who introduced changes on files
# Copyright Edmundo Carmona Antoranz 2017
# Released under the terms of GPLv2

# for starters, will get 2 parameters: two treeishs to compare
# For lines added, will use normal blame operation of the file
# For lines removed, will use reverse blame operation

import subprocess
import sys

def cleanup_filename(filename):
    """
    There could be color markers on the filename... remove them
    """
    index = filename.find(chr(0x1b))
    if index == -1:
        return filename # it's clean
    if index == 0:
        # it' white, right? Let's remove it
        filename=filename[4:]
    else:
        filename=filename[:index]
    return filename

def run_git_command(args):
    """
    Run a git command. If there is an error, will throw an exception. Otherwise, output will be returned
    """
    command = ["git"]
    command.extend(args)
    return subprocess.check_output(command)

def get_blame_info_hunk(blame_opts, treeish, file_name, hunk_position, treeish2=None):
    """
    Get blame for especified hunk
    file_name will remove prepending 'a/' or '/b' if present
    Hunk position says starting line and size of hunk in lines
    
    If treeish2 is set up, it means it's a reverse blame (to get deleted lines)
    """
    if file_name.startswith('a/') or file_name.startswith('b'):
        file_name = file_name[2:]
    hunk_position = hunk_position.split(',')
    
    starting_line=int(hunk_position[0])
    if starting_line == 0:
        return ""
    if starting_line < 0:
        starting_line*=-1
    ending_line=starting_line+int(hunk_position[1])-1
    git_blame_opts=["blame", "--no-progress", "-L", str(starting_line) + "," + str(ending_line)]
    if treeish2 is None:
        # normal blame on treeish1
        git_blame_opts.append(treeish)
    else:
        # reverse blame
        git_blame_opts.extend(["--reverse", treeish2 + ".." + treeish])
    
    if len(blame_opts) > 0:
        git_blame_opts.extend(blame_opts)
    git_blame_opts.extend(["--", file_name])
    return run_git_command(git_blame_opts)

def process_hunk_from_diff_output(blame_params, output_lines, starting_line, original_name, final_name, treeish1, treeish2):
    """
    Process a diff hunk from a file
    A hunk starts with a line that starts with @ and describes the position of the block of code in original file and ending file
        (more datails to come)
    Then we have lines that start with:
        - ' ': Line didn't change
        - '+': Line was added
        - '-': Line was deleted
    Until we have a line that starts with a 'd' or a '@' (begining of new file or begining of new hunk)
    """
    i = starting_line
    hunk_description_line = output_lines[i]
    if len(hunk_description_line) == 0:
        # reached EOF, probably
        return i+1
    
    if hunk_description_line[0] != '@' and not hunk_description_line.startswith(chr(0x1b) + chr(0x5b) + chr(0x33)+ chr(0x36) + chr(0x6d) + "@"):
        # not the begining of a hunk
        raise Exception("Not the begining of a hunk on line " + str(i + 1) + " (" + original_name + ", " + final_name + ")")
    
    # ok.... got a hunk
    print hunk_description_line
    
    hunk_description_info = hunk_description_line.split()
    original_file_hunk_pos = hunk_description_info[1]
    final_file_hunk_pos = hunk_description_info[2]
    
    hunk_lines = []
    # let's get the lines until we get to next hunk, next file or EOF
    i+=1
    while i < len(output_lines) and len(output_lines[i]) > 0 and (output_lines[i][0] in [' ', '+', '-'] or output_lines[i].startswith(chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x32) + chr(0x6d) + '+') or output_lines[i].startswith(chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x31) + chr(0x6d) + '-')):
        # a valid line in the hunk
        hunk_lines.append(output_lines[i])
        i+=1
    
    # let's get blame information for final final
    final_blame=get_blame_info_hunk(blame_params, treeish2, final_name, final_file_hunk_pos).split("\n")
    final_blame_index = 0
    original_blame=get_blame_info_hunk(blame_params, treeish2, final_name, original_file_hunk_pos, treeish1).split("\n")
    original_blame_index = 0
    for line in hunk_lines:
        if line[0] in [' ', '+']:
            # print line from final blame
            print line[0] + final_blame[final_blame_index]
            final_blame_index+=1
            if line[0] == ' ':
                # also move on the original_blame
                original_blame_index+=1
        elif line.startswith(chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x32) + chr(0x6d) + '+'):
            # print line from final blame with color adjusted
            print line[0:6] + final_blame[final_blame_index] + line[-3:]
            final_blame_index+=1
        elif line[0] == '-':
            # it's a line that was deleted so have to pull it from the original_blame
            print line[0] + original_blame[original_blame_index]
            original_blame_index+=1
        elif line.startswith(chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x31) + chr(0x6d) + '-'):
            # print line from final blame with color adjusted
            print line[0:6] + original_blame[original_blame_index] + line[-3:]
            original_blame_index+=1
    
    # hunk is finished (EOF, end of file or end of hunk)
    return i

def process_file_from_diff_output(blame_params, output_lines, starting_line):
    """
    process diff output for a line.
    Will return position of next file in diff outtput
    """
    # First is a 'diff' line
    i=starting_line
    diff_line = output_lines[i].split()
    if diff_line[0] not in ["diff", chr(0x1b) + chr(0x5b) + chr(0x31) + chr(0x6d) + "diff"]:
        raise Exception("Doesn't seem to exist a 'diff' line at line " + str(i + 1) + ": " + output_lines[i])
    original_name = cleanup_filename(diff_line[2])
    final_name = cleanup_filename(diff_line[3])
    print output_lines[i]; i+=1
    
    # let's get to the line that starts with ---
    while i < len(output_lines) and not output_lines[i].startswith("---") and not output_lines[i].startswith(chr(0x1b) + chr(0x5b) + chr(0x31)+ chr(0x6d) + "---"):
        if output_lines[i].startswith("diff") or output_lines[i].startswith(chr(0x1b) + chr(0x5b) + chr(0x31)+ chr(0x6d) + "---"):
            # just finished a file without content changes
            return i
        print output_lines[i]; i+=1
    
    if i >= len(output_lines):
        # a file without content was the last on the patch
        return i
    
    print output_lines[i]; i+=1 # line with ---
    
    # next should begin with +++
    if not output_lines[i].startswith("+++") and not output_lines[i].startswith(chr(0x1b) + chr(0x5b) + chr(0x31)+ chr(0x6d) + "+++"):
        raise Exception("Was expecting line with +++ for a file (" + original_name + ", " + final_name + ")")
    
    print output_lines[i]; i+=1 # line with +++
    
    # Now we start going through the hunks until we don't have a hunk starter mark
    while i < len(output_lines) and len(output_lines[i]) > 0 and (output_lines[i][0]=='@' or output_lines[i].startswith(chr(0x1b) + chr(0x5b) + chr(0x33)+ chr(0x36) + chr(0x6d) + "@")):
        # hunk starts with a @
        i = process_hunk_from_diff_output(blame_params, output_lines, i, original_name, final_name, treeish1, treeish2)
    
    return i

def process_diff_output(blame_params, output, treeish1, treeish2):
    """
    process diff output
    """
    
    # process files until output is finished
    lines=output.split("\n")
    i=0
    while i < len(lines):
        starting_line = lines[i]
        if len(starting_line) == 0:
            # got to the end of the diff output
            break
        i = process_file_from_diff_output(blame_params, lines, i)

# parameters
diff_params=[]
blame_params=[]
treeish1=None
treeish2=None
paths=[]

double_dash=False # haven't found the double dash yet

# process params
for param in sys.argv[1:]:
    if double_dash:
        # it's a file path
        paths.append(param)
    else:
        # haven't found the double dash yet
        if param.startswith('--') or param.startswith("-dp") or param.startswith("-bp"):
            # double dash or parameter
            if (len(param) == 2):
                # it's a --
                double_dash=True
            else:
                if param=="--color":
                    diff_params.append("--color") # use diff color output
                # is it a diff param or a blame param?
                elif param.startswith("--diff-param=") or param.startswith("-dp="):
                    # diff param
                    diff_params.append(param[param.index('=') + 1:])
                elif param.startswith("--blame-param=") or param.startswith("-bp="):
                    blame_params.append(param[param.index('=') + 1:])
                else:
                    sys.stderr.write("Couldn't process option <<" + param + ">>\n")
        else:
            # it's a branch
            treeish1=treeish2
            treeish2=param

# if there's not at least a branch, we can't proceed
if treeish1 is None and treeish2 is None:
    sys.stderr.write("Didn't provide at least a treeish to work on\n")
    sys.exit(1)

if treeish1 is None:
    treeish1 = treeish2
    treeish2 = "HEAD"

diff_output = None
try:
    git_diff_params=["diff"]
    git_diff_params.extend(diff_params)
    git_diff_params.append(treeish1 + ".." + treeish2)
    if len(paths) > 0:
        # only get diff for some paths
        git_diff_params.append('--')
        git_diff_params.extend(paths)
        
    diff_output = run_git_command(git_diff_params)
except:
    print "there was an error running git"
    import traceback
    traceback.print_exc()
    sys.exit(1)

# processing diff output
process_diff_output(blame_params, diff_output, treeish1, treeish2)
