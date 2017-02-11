#!/usr/bin/python

# tool to see who introduced changes on files
# Copyright Edmundo Carmona Antoranz 2017
# Released under the terms of GPLv2

import subprocess
import sys

# color codes
COLOR_GREEN=chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x32) + chr(0x6d)
COLOR_RED=chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x31) + chr(0x6d)
COLOR_WHITE=chr(0x1b) + chr(0x5b) + chr(0x31) + chr(0x6d)
COLOR_RESET=chr(0x1b) + chr(0x5b) + chr(0x6d)

# color diff markers
COLOR_LINE_ADDED_MARKER=COLOR_GREEN + '+'

# general OPTIONS for difflame
# HINTS: use hints (1-line summary of a revision)
# COLOR: use color on output
OPTIONS=dict()
OPTIONS['HINTS']=True # hints by default
OPTIONS['COLOR']=False

# options used for diff and blame
DIFF_OPTIONS=[]
BLAME_OPTIONS=[]


DEBUG_GIT = False
TOTAL_GIT_EXECUTIONS = 0


# caches

# association between revisions and their hints (will be initialized if using hints)
HINTS=None

# association between shortened revision IDs and their real full IDs
REVISIONS_CACHE=dict()

# direct child nodes of each revision
CHILD_REVISIONS_CACHE=dict()

# information displayed for each revision on modified lines
REVISIONS_INFO_CACHE=dict()

class DiffFileObject:
    '''
    Object to hold the content of diff for a file
    
    Will keep 2 things:
        - raw_content: array of lines that make up the raw diff output
        - hunks: array of hunks that make up the diff output
    '''
    
    def __init__(self, starting_revision, final_revision, original_name, final_name, raw_content, hunks):
        self.starting_revision = starting_revision
        self.final_revision = final_revision
        self.original_name = original_name
        self.final_name = final_name
        self.raw_content = raw_content
        self.hunks = hunks # DiffHunk instances

class DiffHunk:
    '''
    Object to hold hunk information
    '''
    def __init__(self, positions, raw_content):
        self.positions = positions
        self.raw_content = raw_content

    def stdoutPrint(self, treeish2, original_file_blame, final_file_blame):
        """
        Print hunk on stdout
        """
        print self.raw_content[0] # hunk descrtiptor line
        previous_revision=None
        for line in self.raw_content[1:]:
            if line[0] in [' ', ]:
                # added line (no color) or unchanged line
                # print line from final blame
                blame_line = final_file_blame.pop(0)
                # move on the original_blame cause we got blame info from final_file_blame
                original_file_blame.pop(0)
                # reset previous revision
                previous_revision=None
                print line[0] + blame_line
            elif line[0] == '+':
                blame_line = final_file_blame.pop(0)
                # have to process revision to see it we need to print hint before the revision
                current_revision = process_added_line(blame_line)
                previous_revision = print_revision_line(current_revision, previous_revision, True)
                # print line from final blame with color adjusted
                if OPTIONS['COLOR']:
                    sys.stdout.write(COLOR_LINE_ADDED_MARKER)
                else:
                    sys.stdout.write('+')
                sys.stdout.write(blame_line)
                if OPTIONS['COLOR']:
                    sys.stdout.write(COLOR_RESET)
                print ""
            elif line[0] == '-':
                # it's a line that was deleted so have to pull it from original_blame
                blame_line = original_file_blame.pop(0)
                # what is the _real_ revision where the lines were deleted?
                (found_real_revision, deletion_revision, original_revision) = process_deleted_line(blame_line, treeish2)
                # print hint if needed
                print_revision_line(deletion_revision, previous_revision, False)
                if found_real_revision:
                    # got the revision where the line was deleted... let's show it
                    print_deleted_revision_info(deletion_revision)
                else:
                    # didn't find the revision where the line was deleted... let's show it with the original revision
                    print_deleted_revision_info(deletion_revision, original_revision)
                # line number and content
                sys.stdout.write(blame_line[blame_line.find(' '):])
                if OPTIONS['COLOR']:
                    sys.stdout.write(COLOR_RESET)
                previous_revision = deletion_revision
                print ""
            elif line[0]=='\\':
                # print original line, nothing is added
                print line
                # reset previous revision
                previous_revision=None
    
    # done printing the hunk
def run_git_command(args):
    global DEBUG_GIT, TOTAL_GIT_EXECUTIONS
    """
    Run a git command. If there is an error, will throw an exception. Otherwise, output will be returned
    """
    command = ["git"]
    command.extend(args)
    if DEBUG_GIT:
        TOTAL_GIT_EXECUTIONS+=1
        sys.stderr.write("git execution: " + str(command) + "\n")
    return subprocess.check_output(command)

def git_revision_hint(revision):
    """
    get revision hint from git (won't include ending \n)
    """
    return run_git_command(["show", "--oneline", "--no-color", "--summary", revision]).split("\n")[0]

def get_full_revision_id(revision):
    """
    Get the full ID of a given ID
    
    First will check in cache to see if the ID had been mapped
    """
    if revision in REVISIONS_CACHE:
        # we already had the revision
        return REVISIONS_CACHE[revision]
    # fallback to get it from git
    full_revision = run_git_command(["show", "--pretty=%H", revision]).split("\n")[0]
    REVISIONS_CACHE[revision] = full_revision
    return full_revision

def get_blame_info_hunk(treeish, file_name, hunk_positions, original_treeish=None):
    """
    Get blame for especified hunk positions
    Prepending 'a/' or '/b' from file_name will be removed if present
    Hunk positions especify starting line and size of hunk in lines
    
    If original_treeish is set up, it means it's a reverse blame to get deleted lines
    """
    # clean up file_name from prepending a/ or b/ (if present)
    if file_name.startswith('a/') or file_name.startswith('b/'):
        file_name = file_name[2:]
    
    # starting to build git command arguments
    git_blame_opts=["blame", "--no-progress"]
    
    for hunk_position in hunk_positions:
        hunk_position = hunk_position.split(',')
        if len(hunk_position) == 1:
            # there was a single number in file position (single line file), let's complete it with a 1
            hunk_position.append("1")
        starting_line=int(hunk_position[0])
        if starting_line == 0:
            # file doesn't exist exist so no content
            return ""
        if starting_line < 0:
            # original file starting line positions in hunk descriptors are negative
            starting_line*=-1
        if len(hunk_position) == 1:
            # single line file
            ending_line = starting_line
        else:
            ending_line=starting_line+int(hunk_position[1])-1
        git_blame_opts.extend(['-L', str(starting_line) + "," + str(ending_line)])
    if original_treeish is None:
        # normal blame on treeish1
        git_blame_opts.append(treeish)
    else:
        # reverse blame
        git_blame_opts.extend(["--reverse", "-s", original_treeish + ".." + treeish])
    
    if len(BLAME_OPTIONS) > 0:
        git_blame_opts.extend(BLAME_OPTIONS)
    git_blame_opts.extend(["--", file_name])
    return run_git_command(git_blame_opts)

def process_hunk_from_diff_output(output_lines, starting_line, original_name, final_name, treeish1, treeish2):
    """
    Process a diff hunk from a file
    A hunk starts with a line that starts with @ and describes the position of the block of code in original file and ending file
        (more datails to come)
    Then we have lines that start with:
        - ' ': Line didn't change
        - '+': Line was added
        - '-': Line was deleted
    Until we have a line that starts with a 'd' or a '@' (begining of new file or begining of new hunk)
    
    Will return a tuple (hunk content [raw] from diff, hunk positions and sizes [original position, final position])
    """
    
    # what will be returned
    hunk_content = []
    
    i = starting_line
    hunk_description_line = output_lines[i]
    if len(hunk_description_line) == 0:
        # reached EOF, probably
        return ("", ["0", "0"]) # return something with the expected structure, just in case
    
    if hunk_description_line[0] != '@':
        # not the begining of a hunk
        raise Exception("Not the begining of a hunk on line " + str(i + 1) + " (" + original_name + ", " + final_name + "): " + hunk_description_line[0])
    
    # description line for a hunk
    hunk_content.append(hunk_description_line)
    
    hunk_description_info = hunk_description_line.split()
    original_file_hunk_pos = hunk_description_info[1]
    final_file_hunk_pos = hunk_description_info[2]

    i+=1
    while i < len(output_lines) and len(output_lines[i]) > 0 and output_lines[i][0] in [' ', '+', '-', '\\']:
        # a valid line in the hunk
        hunk_content.append(output_lines[i])
        i+=1
    
    # got to the end of the hunk
    return DiffHunk([original_file_hunk_pos, final_file_hunk_pos], hunk_content)

def get_revision_from_modified_line(line):
    """
    Return the revision id from an added or removed line
    """
    starting_index = 0
    return line[starting_index:line.index(' ')]

def print_revision_line(current_revision, previous_revision, adding_line):
    """
    Print hint line if hints are enabled
    
    if hints are disabled, nothing will be done
    
    Will check HINTS dictionary for revision.
    If it's not there, will ask git for it and add it to the hints dictionary.
    
    have to return full revision ID
    
    """
    # have to process revision to see it we need to print hint before the revision
    if HINTS is None:
        # not using hints, nothing to do
        return
    
    if previous_revision is not None and current_revision == previous_revision:
        # same revision, nothing to do
        return current_revision
    
    # have to print hint
    hint=None
    if not current_revision in HINTS:
        # have to get hint from git and add it to hints
        hint=git_revision_hint(current_revision)
        HINTS[current_revision]=hint
    else:
        hint=HINTS[current_revision]
    sys.stdout.write("\t")
    if OPTIONS['COLOR']:
        sys.stdout.write(COLOR_WHITE)
    sys.stdout.write(hint)
    if OPTIONS['COLOR']:
        sys.stdout.write(COLOR_RESET)
    print ""
    
    return current_revision

def revisions_pointing(target_revision, starting_from):
    """
    Find revisions that point to target_revision starting to analyze from starting_from
    """
    if target_revision in CHILD_REVISIONS_CACHE:
        # we already had detected the child nodes of this revision
        return CHILD_REVISIONS_CACHE[target_revision]
    git_output=run_git_command(["log", "--pretty=%H%n%P", target_revision + ".." + starting_from]).split("\n")[:-1]
    i=0
    children=[]
    while i < len(git_output):
        if git_output[i+1].find(target_revision) != -1:
            children.append(git_output[i])
        i+=2
    CHILD_REVISIONS_CACHE[target_revision] = children
    return children

def process_added_line(added_line):
    """
    Given a line that was aded, let's find out the revision ID
    """
    # get rid of prefix
    revision = get_revision_from_modified_line(added_line)
    # let's find the real revision ID
    return get_full_revision_id(revision)
    
def process_deleted_line(deleted_line, treeish2):
    """
    Given a line that was deleted, let's find out the revision where it was actually deleted and not its parent (full ID)
    
    Will return a tuple:
        -   deletion revision was found
        -   full id of the revision
            If the revision was found, will return full id of the "real" deletion revision
            Otherwise, will return the reported revision from blame line (in other words, the original revision)
        - original revision as it is on blame line
    """
    # get rid of prefix
    revision = get_revision_from_modified_line(deleted_line)
    original_revision = revision
    if revision.startswith('^'):
        revision = revision[1:]
    # let's find the real revision (among the revisions that point to it) where the line was deleted 'for real')
    full_revision=get_full_revision_id(revision)
    # let's find all revisions that are connected to this revisions starting from treeish2
    revisions_pointing_to=revisions_pointing(full_revision, treeish2)
    # if there's a single revision, BINGO!
    if len(revisions_pointing_to) == 1:
        return (True, revisions_pointing_to[0], original_revision)
    # when many merges are involved, it will take more analysis to figure out
    return (False, full_revision, original_revision)

def print_deleted_revision_info(revision_id, original_revision = None):
    """
    Print revision information for a deleled line
    
    if original_information is provided, that revision will be used on the output for the user to see
        (for example, the real revision of a deletion was not found so using original revision reported)
    """
    info = None
    if revision_id in REVISIONS_INFO_CACHE:
        info = REVISIONS_INFO_CACHE[revision_id]
    else:
        info = run_git_command(["show", "--pretty=%h (%an %ai", revision_id]).split("\n")[0]
        REVISIONS_INFO_CACHE[revision_id] = info
    if OPTIONS['COLOR']:
        sys.stdout.write(COLOR_RED)
    if original_revision is not None:
        sys.stdout.write("%" + original_revision + info[info.index(' '):])
    else:
        sys.stdout.write('-' + info)

def process_file_from_diff_output(output_lines, starting_line, treeish1, treeish2, generate_blame = False):
    """
    process diff output
    Will return a tuple:
        (DiffFileObject corresponding to the file, position (index of line) of next file in diff outtput, original file blame, final file blame)
    """
    # First is a 'diff' line
    raw_content = []
    i=starting_line
    diff_line = output_lines[i].split()
    if diff_line[0] != "diff":
        raise Exception("Doesn't seem to exist a 'diff' line at line " + str(i + 1) + ": " + output_lines[i])
    original_name = diff_line[2]
    final_name = diff_line[3]
    raw_content.append(output_lines[i]); i+=1
    
    # let's get to the line that starts with ---
    while i < len(output_lines) and not output_lines[i].startswith("---"):
        if output_lines[i].startswith("diff"):
            # just finished a file without content changes
            return (DiffFileObject(treeish1, treeish2, original_name, final_name, raw_content, []), i, None)
        raw_content.append(output_lines[i]); i+=1
    
    if i >= len(output_lines):
        # a file without content was the last on the patch
        return (DiffFileObject(treeish1, treeish2, original_name, final_name, raw_content, []), i, None)
    
    raw_content.append(output_lines[i]); i+=1 # line with ---
    
    # next should begin with +++
    if not output_lines[i].startswith("+++"):
        raise Exception("Was expecting line with +++ for a file (" + original_name + ", " + final_name + ")")
    
    raw_content.append(output_lines[i]); i+=1 # line with +++
    
    # Now we start going through the hunks until we don't have a hunk starter mark
    hunks = []
    original_hunk_positions = []
    final_hunk_positions = []
    while i < len(output_lines) and len(output_lines[i]) > 0 and output_lines[i][0]=='@':
        # found hunk mark (@)
        hunk = process_hunk_from_diff_output(output_lines, i, original_name, final_name, treeish1, treeish2)
        hunks.append(hunk)
        original_hunk_positions.append(hunk.positions[0])
        final_hunk_positions.append(hunk.positions[1])
        i+=len(hunk.raw_content)
    
    # pull blame from all hunks
    if generate_blame:
        original_file_blame=get_blame_info_hunk(treeish2, original_name, original_hunk_positions, treeish1).split("\n")
        final_file_blame=get_blame_info_hunk(treeish2, final_name, final_hunk_positions).split("\n")
    else:
        original_file_blame = None
        final_file_blame = None
    
    return (DiffFileObject(treeish1, treeish2, original_name, final_name, raw_content, hunks), i, original_file_blame, final_file_blame)

def print_diff_output(diff_file_object, original_file_blame, final_file_blame):
    '''
    Print the content of the diff for this file (with blame information, the whole package)
    '''
    #Will print starting lines until we hit a starting @ or the content of the diff is finished (no hunks reported)
    i=0
    while i < len(diff_file_object.raw_content) and diff_file_object.raw_content[i][0] != '@':
        print diff_file_object.raw_content[i]
        i+=1
    
    # print hunks
    for hunk in diff_file_object.hunks:
        hunk.stdoutPrint(diff_file_object.final_revision, original_file_blame, final_file_blame)

def process_diff_output(output, treeish1, treeish2):
    global HINTS
    """
    process diff output
    """
    # when using hints, will have a dictionary with the hint of each revision (so that they are only looked for once)
    if OPTIONS['HINTS']:
        HINTS=dict()
    
    # process files until output is finished
    lines=output.split("\n")
    i=0
    
    while i < len(lines):
        starting_line = lines[i]
        if len(starting_line) == 0:
            # got to the end of the diff output
            break
        (diff_file_object, i, original_file_blame, final_file_blame) = process_file_from_diff_output(lines, i, treeish1, treeish2, True)
        print_diff_output(diff_file_object, original_file_blame, final_file_blame)

# parameters
treeish1=None
treeish2=None
paths=[]

double_dash=False # haven't found the double dash yet

# process params
color_set=False # color option hasn't been set by user
for param in sys.argv[1:]:
    if double_dash:
        # it's a file path
        paths.append(param)
    else:
        # haven't found the double dash yet
        if param.startswith('--') or param.startswith("-dp=") or param.startswith("-bp="):
            # double dash or parameter
            if (len(param) == 2):
                # it's a --
                double_dash=True
            else:
                if param in ["--color", "--no-color"]:
                    # set up color output forcibly
                    OPTIONS['COLOR'] = (param == "--color")
                    color_set=True
                # is it a diff param or a blame param?
                elif param.startswith("--diff-param=") or param.startswith("-dp="):
                    # diff param
                    diff_param=param[param.index('=') + 1:]
                    DIFF_OPTIONS.append(diff_param)
                elif param.startswith("--blame-param=") or param.startswith("-bp="):
                    BLAME_OPTIONS.append(param[param.index('=') + 1:])
                elif param in ["--tips", "--hints"]:
                    # Will support them but they are unnecessary
                    continue
                elif param == "--no-hints":
                    OPTIONS['HINTS'] = False
                elif param == "--git-debug":
                    DEBUG_GIT = True
                else:
                    sys.stderr.write("Couldn't process option <<" + param + ">>\n")
        elif param == "-w":
            # avoid space changes
            BLAME_OPTIONS.append(param)
            DIFF_OPTIONS.append(param)
        else:
            # it's a treeish (maybe 2 if using treeish1..treeish2 syntax)
            if treeish1 is not None:
                # already had 2 treeishes set up
                raise Exception("Already have 2 treeishes to work on: " + treeish1 + ".." + treeish2)
            double_dot_index=param.find('..')
            if double_dot_index==-1:
                # single treeish
                treeish1=treeish2
                treeish2=param
            else:
                # passing both treeishes in a single shot
                if treeish2 is not None:
                    # already had at least a treeish set up
                    raise Exception("Already had at least a treeish to work on defined: " + treeish2)
                treeish1=param[0:double_dot_index]
                treeish2=param[double_dot_index+2:]
                

if not color_set:
    # if the user is using a terminal, will use color output
    if sys.stdout.isatty():
        OPTIONS['COLOR'] = True

# if there's not at least a treeish, we can't proceed
if treeish2 is None:
    sys.stderr.write("Didn't provide at least a treeish to work on\n")
    sys.exit(1)

if treeish1 is None:
    treeish1 = treeish2
    treeish2 = "HEAD"

diff_output = None
try:
    git_diff_params=["diff"]
    git_diff_params.append('--no-color')
    git_diff_params.extend(DIFF_OPTIONS)
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
process_diff_output(diff_output, treeish1, treeish2)

if DEBUG_GIT:
    sys.stderr.write("Total git executions: " + str(TOTAL_GIT_EXECUTIONS) + "\n")
