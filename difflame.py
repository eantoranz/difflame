#!/usr/bin/python3

# tool to see who introduced changes on files
# Copyright Edmundo Carmona Antoranz 2017
# Released under the terms of GPLv2

import subprocess
import sys
from time import time
from datetime import datetime

# color codes
COLOR_CYAN=chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x36) + chr(0x6d)
COLOR_GREEN=chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x32) + chr(0x6d)
COLOR_RED=chr(0x1b) + chr(0x5b) + chr(0x33) + chr(0x31) + chr(0x6d)
COLOR_WHITE=chr(0x1b) + chr(0x5b) + chr(0x31) + chr(0x6d)
COLOR_RESET=chr(0x1b) + chr(0x5b) + chr(0x6d)

# general OPTIONS for difflame
# HINTS: use hints (1-line summary of a revision)
# COLOR: use color on output
# SHOWNAME: print name of author
# SHOWMAIL: print mail of author
# SHOWDATE: show date
# PROGRESS: whether to show progress or not
OPTIONS=dict()
OPTIONS['HINTS']=True # hints by default
OPTIONS['COLOR']=False
OPTIONS['SHOWNAME'] = True
OPTIONS['SHOWMAIL'] = False
OPTIONS['SHOWDATE'] = True
OPTIONS['PROGRESS'] = None

# options used for diff and blame
DIFF_OPTIONS=[]
BLAME_OPTIONS=[]

def run_git_command(args):
    global DEBUG_GIT, TOTAL_GIT_EXECUTIONS
    """
    Run a git command. If there is an error, will throw an exception. Otherwise, output will be returned
    """
    command = ["git"]
    command.extend(args)
    if DEBUG_GIT:
        TOTAL_GIT_EXECUTIONS+=1
        commandStr=""
        for word in command:
            commandStr+=word + " "
        sys.stderr.write("git execution: " + str(commandStr) + "...")
        starting_time=time()
    result = subprocess.check_output(command)
    if DEBUG_GIT:
        sys.stderr.write(str((time() - starting_time) * 1000) + " ms\n")
        sys.stderr.flush()
    return result.decode("utf-8")

def run_git_blame(arguments):
    '''
    Run a git blame command. Will return raw output
    '''
    args=["blame", "--no-progress"]
    if len(BLAME_OPTIONS) > 0:
        args.extend(BLAME_OPTIONS)
    args.extend(arguments)
    return run_git_command(args)

def run_git_diff(arguments):
    '''
    Run a git diff command. Will return raw output
    '''
    args=["diff"]
    if len(DIFF_OPTIONS) > 0:
        args.extend(DIFF_OPTIONS)
    args.extend(arguments)
    return run_git_command(args)

DEBUG_GIT = False
TOTAL_GIT_EXECUTIONS = 0

# shortened revision ID length
SHORT_REV_LENGTH=len(run_git_command(["log", "--max-count=1", "--pretty=%h", "HEAD"]).split("\n")[0])

# caches

# association between revisions and their hints (will be initialized if using hints)
HINTS=None

# association between shortened revision IDs and their real full IDs
REVISIONS_CACHE=dict()

# direct parent nodes of each revision
PARENT_REVISIONS_CACHE=dict() # TODO does it have to be calculated depending on the path that is being analyzed?

'''
information displayed for each revision on modified lines
- shortened-id
- author
- author_mail
- author_time
- author_tz
- committer
- committer_mail
- committer_time
- committer_tz
- summary

use get_revision_info(full-rev-id)
'''
REVISIONS_INFO_CACHE=dict()

def get_revision_info(full_id):
    '''
    Pull information about a revision
    
    if the revision is not present, information will be pulled from git
    '''
    if full_id not in REVISIONS_INFO_CACHE:
        # information was not present.... have to pull it from git
        values = dict()
        values['revision'] = full_id
        output = run_git_command(["cat-file", "-p", full_id]).split("\n")
        summary_next = False
        for line in output:
            if summary_next:
                # this line is the summary
                values['summary'] = line
                break # that's it
            if len(line) == 0:
                summary_next = True
            else:
                separator_index = line.index(' ')
                field = line[:separator_index]
                if field == 'author':
                    email_start_index = line.index('<')
                    values['author'] = line[separator_index + 1:email_start_index - 1]
                    separator_index = line.index('>')
                    values['author_mail'] = line[email_start_index + 1:separator_index]
                    temp = line.split(" ")
                    values['author_time'] = temp[-2]
                    values['author_tz'] = temp[-1]
                elif field == 'committer':
                    email_start_index = line.index('<')
                    values['committer'] = line[separator_index + 1:email_start_index - 1]
                    separator_index = line.index('>')
                    values['committer_mail'] = line[email_start_index + 1:separator_index]
                    temp = line.split(" ")
                    values['committer_time'] = temp[-2]
                    values['committer_tz'] = temp[-1]
        REVISIONS_INFO_CACHE[full_id] = values
    return REVISIONS_INFO_CACHE[full_id]

def set_revision_information(full_id, author, author_mail, author_time, author_tz,
                             committer, committer_mail, committer_time, committer_tz,
                             summary):
    '''
    Save revision information (if it wasn't already saved)
    '''
    if full_id not in REVISIONS_INFO_CACHE:
        values = dict()
        values['revision'] = full_id
        values['author'] = author
        values['author_mail'] = author_mail
        values['author_time'] = author_time
        values['author_tz'] = author_tz
        values['committer'] = committer
        values['committer_mail'] = committer_mail
        values['committer_time'] = committer_time
        values['committer_tz'] = committer_tz
        values['summary'] = summary
        REVISIONS_INFO_CACHE[full_id] = values

'''
caches to save:
    - diff of files when analyzing revisions (merges and so on)
    - revisions between 2 revisions (treeish1..treeish2)
    - full revision ID corresponding to some treeish (tag, short revision ID, etc)

DIFF_FILES_CACHE[originating_revision][final_revision][filename] = diff_file_object
use get_line_in_revision()

REVISIONS_CACHE[treeish1][treeish2]
use get_revisions()

REVISIONS_ID_CACHE[treeish]
use get_full_revision_id()

'''
DIFF_FILES_CACHE = None
REVISIONS_CACHE = dict()
REVISIONS_ID_CACHE = dict()

class DiffFileObject:
    '''
    Object to hold the content of diff for a file
    
    Will keep many things:
        - revision where the diff 'started' and 'ended' (started..ended)
        - original filename,
        - final filename
        - raw_content: array of lines that make up the raw diff output
        - hunks: array of hunks that make up the diff output
        - original hunks positions # TODO consider moving this into each hunk
        - final hunks positions # TODO consider moving this into each hunk
            Hunk positions are used only when blaming the lines (not always necessary)
    '''
    
    def __init__(self, starting_revision, final_revision, original_name, final_name, raw_content, hunks, original_hunk_positions = None, final_hunk_positions = None):
        self.starting_revision = starting_revision
        self.final_revision = final_revision
        self.original_name = original_name
        self.final_name = final_name
        self.raw_content = raw_content
        self.hunks = hunks # DiffHunk instances
        self.original_hunk_positions = original_hunk_positions
        self.final_hunk_positions = final_hunk_positions
        
        # let's make hunks point to this diff instance
        for hunk in hunks:
            hunk.diff_file_object = self
    
    def getOriginalFileBlame(self, reverse):
        if len(self.hunks) == 0:
            # let's not care about it cause it's probably a binary file
            return ""
        return self.get_blame_info_hunk(True, reverse).split("\n")
    
    def getFinalFileBlame(self, reverse):
        return self.get_blame_info_hunk(False, reverse).split("\n")

    def get_blame_info_hunk(self, reverse_blame, reverse_analysis):
        """
        Get blame for especified hunk positions
        Prepending 'a/' or '/b' from file_name will be removed if present
        Hunk positions especify starting line and size of hunk in lines
        
        reverse_blame specifies if it will be 
        """
        # clean up file_name from prepending a/ or b/ (if present)
        if reverse_blame:
            file_name = self.original_name
            if reverse_analysis:
                hunk_positions = self.final_hunk_positions
            else:
                hunk_positions = self.original_hunk_positions
        else:
            file_name = self.final_name
            if reverse_analysis:
                hunk_positions = self.original_hunk_positions
            else:
                hunk_positions = self.final_hunk_positions
        
        file_name = cleanup_filename(file_name)
        
        # starting to build git command arguments
        git_blame_opts = ["--line-porcelain"]
        
        if hunk_positions is not None:
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
        if not reverse_blame:
            # normal blame on final_revision
            if reverse_analysis:
                git_blame_opts.append(self.starting_revision)
            else:
                git_blame_opts.append(self.final_revision)
        else:
            # reverse blame
            git_blame_opts.append("--reverse")
            if reverse_analysis:
                git_blame_opts.extend([self.final_revision + ".." + self.starting_revision])
            else:
                git_blame_opts.extend([self.starting_revision + ".." + self.final_revision])
        
        git_blame_opts.extend(["--", file_name])
        return run_git_blame(git_blame_opts)

    def process(self, reverse):
        '''
        Process the content of the diff for this file (with blame information, the whole package)
        
        If reverse, "blaming analysis" has to be performed treeish2..treeish1
        '''
        #Will print starting lines until we hit a starting @ or the content of the diff is finished (no hunks reported)
        original_file_blame = self.getOriginalFileBlame(reverse)
        final_file_blame = self.getFinalFileBlame(reverse)
        for hunk in self.hunks:
            hunk.processHunk(original_file_blame, final_file_blame, reverse)
    
    def stdoutPrint(self, reverse, max_name_width, max_mail_width, starting_line_width, final_line_width):
        '''
        Print Diff Object
        '''
        i=0
        while i < len(self.raw_content) and len(self.raw_content[i]) and self.raw_content[i][0] != '@':
            if OPTIONS['COLOR']:
                sys.stdout.write(COLOR_WHITE)
            sys.stdout.write(self.raw_content[i])
            if OPTIONS['COLOR']:
                sys.stdout.write(COLOR_RESET)
            print("")
            i+=1
        
        if len(self.hunks) == 0:
            # no hunks.... binary file probably
            return
        
        for hunk in self.hunks:
            hunk.printLines(reverse, max_name_width, max_mail_width, starting_line_width, final_line_width)
    
    def getMaxNameWidth(self):
        '''
        Max width of author name
        '''
        max_width = 0
        for hunk in self.hunks:
            if hunk.max_author_width > max_width:
                max_width = hunk.max_author_width
        return max_width

    def getMaxMailWidth(self):
        '''
        Max Mail Width
        '''
        max_width = 0
        for hunk in self.hunks:
            if hunk.max_mail_width > max_width:
                max_width = hunk.max_mail_width
        return max_width
    
    def getMaxStartingLine(self):
        '''
        Get the maximum original line
        '''
        max_line = None
        if len(self.hunks) > 0:
            max_line = self.hunks[-1].max_starting_line
        if max_line is None:
            max_line = 0
        return max_line
    
    def getMaxFinalLine(self):
        '''
        Get the maximum original line
        '''
        max_line = None
        if len(self.hunks) > 0:
            max_line = self.hunks[-1].max_final_line
        if max_line is None:
            max_line = 0
        return max_line
        
    
class HunkLine:
    '''
    Structure to hold information for a line on the hunk:
    - Added:
        Whether the line was added (True), removed (False), or left as is (None)
    - Revision
    - Filename
    - Content
    '''
    
    def __init__(self, added, revision, filename, content):
        self.added = added
        self.revision = revision
        self.filename = filename
        self.content = content

class DiffHunk:
    '''
    Object to hold hunk information
    '''
    def __init__(self, positions, raw_content):
        self.positions = positions
        
        original_pos = positions[0].split(",")
        self.original_file_starting_line = abs(int(original_pos[0]))
        # the ending line is the first line _after_ the hunk
        if len(original_pos) == 1:
            # only had a single line in the block
            self.original_file_ending_line = self.original_file_starting_line + 1
        else:
            self.original_file_ending_line = self.original_file_starting_line + int(original_pos[1])
        final_pos = positions[1].split(",")
        self.final_file_starting_line = abs(int(final_pos[0]))
        # the ending line is the first line _after_ the hunk
        if len(final_pos) == 1:
            # only had a single line in the block
            self.final_file_ending_line = self.final_file_starting_line + 1
        else:
            self.final_file_ending_line = self.final_file_starting_line + int(final_pos[1])
        
        self.raw_content = raw_content
        # in what line (of raw content), does 'real content' start?
        self.content_starting_index = None
        i=0
        while i < len(self.raw_content):
            if self.raw_content[i][0] != '@':
                # here is where content starts 'for real'
                self.content_starting_index = i
                break
            i+=1
        
        self.lines = None
        
        self.max_author_width = 0 # maximum width for an author name
        self.max_mail_width = 0 # max width for an author email
        # max line number (for formatting)
        self.max_starting_line = None
        self.max_final_line = None
    
    def printLines(self, reverse, max_author_width, max_mail_width, starting_line_width, final_line_width):
        '''
        Print all lines (it will eventually include params to control output width and so on)
        '''
        starting_line_number = self.original_file_starting_line
        final_line_number = self.final_file_starting_line
        previous_revision = None
        self.printDescriptorLine()
        for line in self.lines:
            if isinstance(line, HunkLine):
                if OPTIONS['HINTS'] or OPTIONS['SHOWNAME'] or OPTIONS['SHOWMAIL'] or OPTIONS['SHOWDATE']:
                    revision_info = get_revision_info(line.revision)
                if OPTIONS['HINTS']:
                    # hints are being printed
                    if line.added is not None:
                        # line is added or deleted
                        if previous_revision is None or previous_revision != line.revision:
                            # have to print the hink
                            if OPTIONS['COLOR']:
                                sys.stdout.write(COLOR_WHITE)
                            sys.stdout.write("\t" + line.revision[:SHORT_REV_LENGTH] + ": " + revision_info['summary'])
                            if OPTIONS['COLOR']:
                                sys.stdout.write(COLOR_RESET)
                            sys.stdout.write("\n")
                            previous_revision = line.revision
                    else:
                        previous_revision = None
                if line.added is None:
                    sys.stdout.write(' ')
                elif not reverse and line.added or reverse and not line.added:
                    if OPTIONS['COLOR']:
                        sys.stdout.write(COLOR_GREEN)
                    sys.stdout.write('+')
                elif not reverse and not line.added or reverse and line.added:
                    if OPTIONS['COLOR']:
                        sys.stdout.write(COLOR_RED)
                    sys.stdout.write('-')
                sys.stdout.write(line.revision[:SHORT_REV_LENGTH] + ' ')
                if OPTIONS['SHOWNAME'] or OPTIONS['SHOWMAIL']:
                    sys.stdout.write('(')
                if OPTIONS['SHOWNAME']:
                    sys.stdout.write(revision_info['author'] + (' ' * (max_author_width - len(revision_info['author']))) + ' ')
                if OPTIONS['SHOWMAIL']:
                    sys.stdout.write('<' + revision_info['author_mail'] + '>' + (' ' * (max_mail_width - len(revision_info['author_mail']))) + ' ')
                if OPTIONS['SHOWDATE']:
                    sys.stdout.write(str(datetime.fromtimestamp(int(revision_info['author_time']))) + ' ')
                if line.added is None or not reverse and not line.added or reverse and line.added:
                    sys.stdout.write(("%" + str(starting_line_width) + "d") % starting_line_number)
                    starting_line_number += 1
                else:
                    sys.stdout.write(' ' * starting_line_width)
                sys.stdout.write(' ')
                if line.added is None or not reverse and line.added or reverse and not line.added:
                    sys.stdout.write(("%" + str(final_line_width) + "d") % final_line_number)
                    final_line_number += 1
                else:
                    sys.stdout.write(' ' * final_line_width)
                sys.stdout.write(') ' + line.content)
                if OPTIONS['COLOR']:
                    sys.stdout.write(COLOR_RESET)
                print()
            else:
                print(line)
            sys.stdout.flush()
    
    def printDescriptorLine(self):
        '''
        Print hunk description line
        '''
        if OPTIONS['COLOR']:
            sys.stdout.write(COLOR_CYAN)
            index_of_separation = self.raw_content[0].index('@@', 2)
            sys.stdout.write(self.raw_content[0][:index_of_separation + 2])
            sys.stdout.write(COLOR_RESET)
            sys.stdout.write(self.raw_content[0][index_of_separation+2:])
            print("")
        else:
            print(self.raw_content[0]) # hunk descriptor line
    
    def processHunk(self, original_file_blame, final_file_blame, reverse):
        lines = []
        """
        analyze hunk and save its lines
        """
        starting_line_number = self.original_file_starting_line
        ending_line_number = self.final_file_starting_line
        if reverse:
            starting_revision = self.diff_file_object.final_revision
            target_revision = self.diff_file_object.starting_revision
        else:
            starting_revision = self.diff_file_object.starting_revision
            target_revision = self.diff_file_object.final_revision
        for line in self.raw_content[1:]:
            if line[0] == ' ':
                # unchanged line
                final_line = self.readPorcelainLine(final_file_blame)
                # move on the original_blame cause we got blame info from final_file_blame
                original_line = self.readPorcelainLine(original_file_blame)
                self.max_starting_line = starting_line_number
                self.max_final_line = ending_line_number
                lines.append(HunkLine(None, final_line['revision'], final_line['filename'], final_line['content']))
                starting_line_number += 1
                ending_line_number += 1
            elif not reverse and line[0] == '+' or reverse and line[0] == '-':
                final_line = self.readPorcelainLine(final_file_blame)
                self.max_final_line = ending_line_number
                lines.append(HunkLine(True, final_line['revision'], final_line['filename'], final_line['content']))
                ending_line_number += 1
            elif not reverse and line[0] == '-' or reverse and line[0] == '+':
                # it's a line that was deleted so have to pull it from original_blame
                original_line = self.readPorcelainLine(original_file_blame)
                # what is the _real_ revision where the lines were deleted?
                self.max_starting_line = starting_line_number
                if reverse:
                    deleted_line_number = original_line['final_line']
                else:
                    deleted_line_number = original_line['original_line']
                revision = original_line['revision']
                deletion_revision = process_deleted_line(starting_revision, target_revision, original_line['filename'], deleted_line_number)
                # print hint if needed
                if deletion_revision is None:
                    hunk_line = HunkLine(False, revision, original_line['filename'], original_line['content'])
                else:
                    hunk_line = HunkLine(False, deletion_revision, original_line['filename'], original_line['content'])
                lines.append(hunk_line)
                starting_line_number += 1
            if line[0]=='\\':
                lines.append(line)
            else:
                # HunkLine is already in
                if OPTIONS['SHOWNAME'] or OPTIONS['SHOWMAIL']:
                    revision_info = get_revision_info(lines[-1].revision)
                    author_width = len(revision_info['author'])
                    mail_width = len(revision_info['author_mail'])
                    if author_width > self.max_author_width:
                        self.max_author_width = author_width
                    if mail_width > self.max_mail_width:
                        self.max_mail_width = mail_width
        
        self.lines = lines

    def readPorcelainLine(self, porcelainOutput):
        '''
        Read the content of a blame --line-porcelain.
        Will return a dict with the following keys:
        - revision (full ID)
        - original_line
        - final_line
        - author
        - author-mail
        - author-time
        - author-tz
        - committer
        - committer-mail
        - committer-time
        - committer-tz
        - summary
        - previous
        - filename
        - boundary (True, False)
        - content
        '''
        values = dict()
        temp = porcelainOutput.pop(0).split(" ")
        values['revision'] = temp[0]
        values['original_line'] = int(temp[1])
        values['final_line'] = int(temp[2])
        values['boundary'] = False
        
        while True:
            line = porcelainOutput.pop(0)
            if line[0] == '\t':
                # content line
                values['content'] = line[1:]
                break
            else:
                if line == 'boundary':
                    values['boundary'] = True
                    continue
                separator = line.index(' ')
                field = line[:separator]
                value = line[separator + 1:]
                values[field] = value
        
        # save in cache if we don't have information about the revision yet
        set_revision_information(values['revision'], values['author'], values['author-mail'][1:-1], values['author-time'], values['author-tz'],
                             values['committer'], values['committer-mail'][1:-1], values['committer-time'], values['committer-tz'],
                             values['summary'])
        return values

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
    # if revision has a prepending '^', we strip it
    if revision[0] == '^':
        revision = revision[1:]
    if revision in REVISIONS_ID_CACHE:
        # we already had the revision
        return REVISIONS_ID_CACHE[revision]
    # fallback to get it from git
    full_revision = run_git_command(["rev-parse", revision]).split("\n")[0]
    REVISIONS_ID_CACHE[revision] = full_revision
    return full_revision

def get_revisions(treeish1, treeish2, filename = None):
    '''
    get the list of revisions that are part of treeish2
    and that _do not_ belong to treeish1
    '''
    if treeish1 not in REVISIONS_CACHE:
        REVISIONS_CACHE[treeish1] = dict()
    if treeish2 not in REVISIONS_CACHE[treeish1]:
        REVISIONS_CACHE[treeish1][treeish2] = dict()
    if filename not in REVISIONS_CACHE[treeish1][treeish2]:
        if filename is None:
            output=run_git_command(["log", "--pretty=%H", treeish1 + ".." + treeish2])
        else:
            output=run_git_command(["log", "--pretty=%H", treeish1 + ".." + treeish2, "--", filename])
        REVISIONS_CACHE[treeish1][treeish2][filename] = output.split("\n")
    return REVISIONS_CACHE[treeish1][treeish2][filename]

def cleanup_filename(filename):
    '''
    Removing prepending a/ or b/ if present
    '''
    if len(filename) >= 2 and filename[0] in ['a', 'b'] and filename[1] == '/':
        return filename[2:]
    return filename

def process_hunk_from_diff_output(output_lines, starting_line, original_name, final_name):
    """
    Process a diff hunk from a file
    A hunk starts with a line that starts with @ and describes the position of the block of code in original file and ending file
        (more datails to come)
    Then we have lines that start with:
        - ' ': Line didn't change
        - '+': Line was added
        - '-': Line was deleted
    Until we have a line that starts with a 'd' or a '@' (beginning of new file or begining of new hunk)
    
    Will return a tuple (hunk content [raw] from diff, hunk positions and sizes [original position, final position])
    """
    
    # what will be returned
    hunk_content = []
    
    i = starting_line
    hunk_description_line = output_lines[i]
    if len(hunk_description_line) == 0:
        # reached EOF, probably
        return DiffHunk(["0", "0"], []) # return something with the expected structure, just in case
    
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
    print("")
    
    return current_revision

def get_parent_revisions(revision):
    """
    Find the parent revisions of a given revision
    """
    if revision in PARENT_REVISIONS_CACHE:
        return PARENT_REVISIONS_CACHE[revision]
    # didn't have the parent revisions
    parents=run_git_command(["log", "--pretty=%P", revision]).split("\n")[0].split(" ")
    PARENT_REVISIONS_CACHE[revision] = parents
    return parents

def process_added_line(added_line):
    """
    Given a line that was aded, let's find out the revision ID
    """
    # get rid of prefix
    revision = get_revision_from_modified_line(added_line)
    # let's find the real revision ID
    return get_full_revision_id(revision)

def get_line_number_from_deleted_line(deleted_line):
    '''
    line number will always come right before a ')'
    '''
    parenthesis_index = deleted_line.index(')')
    # now we go back until we find anything not in [0-9]
    i = parenthesis_index-1
    while deleted_line[i] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
        i-=1
    return int(deleted_line[i+1:parenthesis_index])

def get_line_in_revision(original_revision, final_revision, filename, line_number):
    '''
    Get the line number for final_revision of the line that was line_number on original_revision
    filename has to be the name of the file on the _final_revision_
    
    If the line is not present anymore (was deleted), will return None
    '''
    # let's create a hunk from the diff
    if original_revision not in DIFF_FILES_CACHE:
        DIFF_FILES_CACHE[original_revision] = dict()
    if final_revision not in DIFF_FILES_CACHE[original_revision]:
        DIFF_FILES_CACHE[original_revision][final_revision] = dict()
    if filename not in DIFF_FILES_CACHE[original_revision][final_revision]:
        output = run_git_diff(["--no-color", original_revision + ".." + final_revision, "--", filename]).split("\n")
        (diff_object, i) = process_file_from_diff_output(output, 0, original_revision, final_revision)
        DIFF_FILES_CACHE[original_revision][final_revision][filename] = diff_object
    
    diff_object = DIFF_FILES_CACHE[original_revision][final_revision][filename]
    if diff_object is None:
        # no change
        return line_number
    
    line_diff=0 # the difference in line numbers between original file and final file
    for hunk in diff_object.hunks:
        if line_number < hunk.original_file_starting_line:
            # the line did survive.... have to return the line number from the originating file plus line_diff
            return line_number + line_diff
        
        if line_number >= hunk.original_file_starting_line and line_number < hunk.original_file_ending_line:
            # the line that is being asked to be checked is included in this hunk
            original_line_number = hunk.original_file_starting_line
            final_line_number = hunk.final_file_starting_line
            i=hunk.content_starting_index
            while i < len(hunk.raw_content):
                line = hunk.raw_content[i]
                if line_number == original_line_number:
                    # this is the line that matters
                    if line[0] == '-':
                        # line was deleted
                        return None
                    if line[0] == ' ':
                        # line has the number as in final_line_number
                        return final_line_number
                if line[0] in [' ', '+']:
                    final_line_number+=1
                if line[0] in [' ', '-']:
                    original_line_number+=1
                # next line from hunk
                i+=1
            raise Exception('We shouldn\'t have reached this point')
        line_diff=hunk.final_file_ending_line - hunk.original_file_ending_line
    # If we reached this point, the line survived
    return line_number + line_diff

def process_deleted_line(starting_revision, target_revision, original_filename, deleted_line_number):
    '''
    Manually find the revision in the history of treeish2 where the line reported was deleted (in relation to treeish1)
    This will be called when treeish1 is _not_ part of the history of treeish2
    
    If a revision could not be found, will return None (for recursion purposes)
    
    revisions_treeish2 are the revisions that are exclusive for treeish2 (not present in the history of treeish1)
    '''
    # find _all_ revisions that are part of "target" revision that are not part of the history of "starting" revision
    revisions_target=get_revisions(starting_revision, target_revision)
    # TODO find the name of the file on treeish2
    revisions_for_file=get_revisions(starting_revision, target_revision, original_filename)
    if len(revisions_for_file) == 0:
        return None
    revision=revisions_for_file[0]
    '''
    on revision, the line must be _gone_.
    If it is _not_ gone, then the deleting revision was on a previous (recursive call)
    '''
    line_in_revision = get_line_in_revision(starting_revision, revision, original_filename, deleted_line_number)
    if line_in_revision is not None:
        #Line is not deleted on this revision.... returning None
        return None
    # if in all parents (that are _not_ part of treeish1) the line is gone, then we found the revision where it was deleted
    for parent in get_parent_revisions(revision):
        if parent not in revisions_target:
            #Parent is in the history of treeish1, discarding for analysis
            continue
        line_in_revision = get_line_in_revision(starting_revision, parent, original_filename, deleted_line_number)
        if line_in_revision is None:
            #Line is _not_ included in this parent... going into this parent
            result = process_deleted_line(starting_revision, parent, original_filename, deleted_line_number)
            if result is not None:
                return result
    # if we reached this point, we ran out of parents... this is the culprit revision
    return revision
    
def process_file_from_diff_output(output_lines, starting_line, treeish1, treeish2):
    """
    process diff output
    Will return a tuple:
        (DiffFileObject corresponding to the file, position (index of line) of next file in diff outtput)
    """
    # First is a 'diff' line
    raw_content = []
    i=starting_line
    diff_line = output_lines[i].split()
    if len(diff_line) == 0:
        # probably no difference
        return (None, starting_line)
    if diff_line[0] != "diff":
        raise Exception("Doesn't seem to exist a 'diff' line at line " + str(i + 1) + ": " + output_lines[i])
    original_name = diff_line[2]
    final_name = diff_line[3]
    raw_content.append(output_lines[i]); i+=1
    
    # let's get to the line that starts with ---
    while i < len(output_lines) and not output_lines[i].startswith("---"):
        if output_lines[i].startswith("diff"):
            # just finished a file without content changes
            return (DiffFileObject(treeish1, treeish2, original_name, final_name, raw_content, []), i)
        raw_content.append(output_lines[i]); i+=1
    
    if i >= len(output_lines):
        # a file without content was the last on the patch
        return (DiffFileObject(treeish1, treeish2, original_name, final_name, raw_content, []), i)
    
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
        hunk = process_hunk_from_diff_output(output_lines, i, original_name, final_name)
        hunks.append(hunk)
        original_hunk_positions.append(hunk.positions[0])
        final_hunk_positions.append(hunk.positions[1])
        i+=len(hunk.raw_content)
    
    return (DiffFileObject(treeish1, treeish2, original_name, final_name, raw_content, hunks, original_hunk_positions, final_hunk_positions), i)

def process_diff_output(output, treeish1, treeish2):
    """
    process diff output
    """
    # when using hints, will have a dictionary with the hint of each revision (so that they are only looked for once)
    global HINTS, BLAMED_FILES_CACHE, DIFF_FILES_CACHE
    if OPTIONS['HINTS']:
        HINTS=dict()
    
    # process files until output is finished
    lines=output.split("\n")
    i=0
    
    reverse = False
    merge_base = run_git_command(["merge-base", treeish1, treeish2]).split("\n")[0]
    if merge_base == treeish2:
        reverse = True
    
    diff_file_objects = []
    max_name_width = 0
    max_mail_width = 0
    max_starting_line = 0
    max_final_line = 0
    while i < len(lines):
        if OPTIONS['PROGRESS']:
            sys.stderr.write(chr(13) + "Processing line " + str(i) + "/" + str(len(lines)))
            sys.stderr.flush()
        starting_line = lines[i]
        if len(starting_line) == 0:
            # got to the end of the diff output
            break
        BLAMED_FILES_CACHE=dict()
        DIFF_FILES_CACHE=dict()
        (diff_file_object, i) = process_file_from_diff_output(lines, i, treeish1, treeish2)
        diff_file_object.process(reverse)
        temp = diff_file_object.getMaxNameWidth()
        if temp > max_name_width:
            max_name_width = temp
        temp = diff_file_object.getMaxMailWidth()
        if temp > max_mail_width:
            max_mail_width = temp
        temp = diff_file_object.getMaxStartingLine()
        if temp > max_starting_line:
            max_starting_line = temp
        temp = diff_file_object.getMaxFinalLine()
        if temp > max_final_line:
            max_final_line = temp
        diff_file_objects.append(diff_file_object)
    
    if OPTIONS['PROGRESS']:
        sys.stderr.write(chr(13) + "Processing line " + str(len(lines)) + "/" + str(len(lines)) + "\n")
    
    for diff_file_object in diff_file_objects:
        diff_file_object.stdoutPrint(reverse, max_name_width, max_mail_width, len(str(max_starting_line)), len(str(max_final_line)))

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
                    blame_param = param[param.index('=') + 1:]
                    if blame_param == "-e":
                        OPTIONS['SHOWNAME'] = False
                        OPTIONS['SHOWMAIL'] = True
                    elif blame_param == "-s":
                        OPTIONS['SHOWNAME'] = False
                        OPTIONS['SHOWMAIL'] = False
                        OPTIONS['SHOWDATE'] = False
                    else:
                        BLAME_OPTIONS.append()
                elif param in ["--tips", "--hints"]:
                    # Will support them but they are unnecessary
                    continue
                elif param == "--no-hints":
                    OPTIONS['HINTS'] = False
                elif param == "--git-debug":
                    DEBUG_GIT = True
                elif param == "--progress":
                    OPTIONS['PROGRESS'] = True
                elif param == "--no-progress":
                    OPTIONS['PROGRESS'] = False
                else:
                    sys.stderr.write("Couldn't process option <<" + param + ">>\n")
        elif param == "-w":
            # avoid space changes
            BLAME_OPTIONS.append(param)
            DIFF_OPTIONS.append(param)
        elif param == "-e":
            OPTIONS['SHOWNAME'] = False
            OPTIONS['SHOWMAIL'] = True
        elif param == "-s":
            OPTIONS['SHOWNAME'] = False
            OPTIONS['SHOWMAIL'] = False
            OPTIONS['SHOWDATE'] = False
        else:
            # it's a treeish (maybe 2 if using treeish1..treeish2 syntax)
            if treeish1 is not None:
                # already had 2 treeishes set up
                raise Exception("Already have 2 treeishes to work on: " + treeish1 + ".." + treeish2)
            double_dot_index=param.find('..')
            if double_dot_index==-1:
                # single treeish
                treeish1=treeish2
                treeish2=get_full_revision_id(param)
            else:
                # passing both treeishes in a single shot
                if treeish2 is not None:
                    # already had at least a treeish set up
                    raise Exception("Already had at least a treeish to work on defined: " + treeish2)
                treeish1=get_full_revision_id(param[0:double_dot_index])
                treeish2=get_full_revision_id(param[double_dot_index+2:])
                

if not color_set:
    # if the user is using a terminal, will use color output
    if sys.stdout.isatty():
        OPTIONS['COLOR'] = True

if OPTIONS['PROGRESS'] is None:
    OPTIONS['PROGRESS'] = sys.stderr.isatty()

# if there's not at least a treeish, we can't proceed
if treeish2 is None:
    sys.stderr.write("Didn't provide at least a treeish to work on\n")
    sys.exit(1)

if treeish1 is None:
    treeish1 = treeish2
    treeish2 = get_full_revision_id("HEAD")

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
    print("there was an error running git")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# processing diff output
process_diff_output(diff_output, treeish1, treeish2)

if DEBUG_GIT:
    sys.stderr.write("Total git executions: " + str(TOTAL_GIT_EXECUTIONS) + "\n")

sys.stderr.flush()
sys.stderr.close()
sys.stdout.flush()
sys.stdout.close()
