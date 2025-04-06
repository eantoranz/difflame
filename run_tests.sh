#!/bin/bash

# this script will setup history over which we will run tests
# copyright 2025 Edmundo Carmona Antoranz
# released under the terms for GPLv2

function check_difflame {
  # parameters
  # - starting commit
  # - final commit
  # - revision to check
  # - expected added lines
  # - expected removed lines
  echo -n "Running test for changes from revision $3 in difflame $1..$2: "
  added_lines=$( ../difflame --no-progress $1 $2 | grep "^+$3" | wc -l )
  test $added_lines -eq $4 || (
    echo FAILED
    echo Check for added lines failed: $1..$2, $3, expected $4 lines added, got $added_lines
    ../difflame --no-progress --no-hints $1 $2 | grep "$3"
    exit 1
  )
  removed_lines=$( ../difflame --no-progress $1 $2 | grep "^-$3" | wc -l )
  test $removed_lines -eq $5 || (
    echo FAILED
    echo Check for added lines failed: $1..$2, $3, expected $5 lines removed, got $removed_lines
    ../difflame --no-progress --no-hints $1 $2 | grep "$3"
    exit 1
  )
  echo OK
}

if [ ! -f run_tests.sh ]; then
  echo It looks like you are not running this script from difflame\'s root dorectory.
  echo Please, go there and try again by running ./run_tests.sh
  exit 1
fi

if [ -d test ]; then
  echo test directory already exists. Please, remove it "(or rename it)" so the tests can be run: rm -fR test
  exit 1
fi

set -e

mkdir test
cd test

git init . -b test # fix the name of branch we will be working on

export GIT_AUTHOR_NAME="fulano"
export GIT_AUTHOR_EMAIL="<fulano>"
export GIT_COMMITTER_NAME="mengano"
export GIT_COMMITTER_EMAIL="<mengano>"

# first commit will hold a file with 100 numbers
i=1; while [ $i -le 100 ]; do
  echo $i >> numbers.txt
  i=$(( $i + 1 ))
done
git add numbers.txt
git commit -m "first commit, numbers 1 to 100"
git branch first-commit

# modify a couple of numbers
sed -i 's/^50$/150/;s/^60$/601/' numbers.txt
git add numbers.txt
git commit -m "second commit, modified 50 and 60"

# remove a few numbers
sed -i '/^7.$/d' numbers.txt
git add numbers.txt
git commit -m "third commit, removed numbers 70-79"

# add a few lines
sed -i '/11/i120\n125\n128' numbers.txt
git add numbers.txt
git commit -m "fourth commit, inserted a few numbers"

# let's branch off and do a merge that includes a change
git branch branch1
git branch branch2

git checkout branch1
sed -i 's/^80$/180/;s/^90$/901/' numbers.txt
git add numbers.txt
git commit -m "first commit in branch1 - modified numbers 80 and 90"

git checkout branch2
sed -i '/^3[1-5]$/d' numbers.txt
git add numbers.txt
git commit -m "first commit in branch2: removed numbers 31-35"

git checkout test
git merge branch1 # this should be a fast-forward

git merge --no-commit branch2 # there should be no conflict here
# let's add a few lines by the end of the file
i=1000; while [ $i -lt 1010 ]; do
  echo $i >> numbers.txt
  i=$(( $i + 1 ))
done
sed -i '/^1[1-5]$/d' numbers.txt # removed numbers 1/5
sed -i 's/^42$/1042/;s/^43$/2043/' numbers.txt # modified 2 numbers
git add numbers.txt
git commit -m "merge commit, adding numbers 1000..1009, removed numbers 11-15, modified 42 and 43"

echo test commit chart:
git log --oneline --graph

# let's test what we have
# from last commit, 3 lines were added
check_difflame first-commit test $( git rev-parse --short @ ) 12 7

check_difflame first-commit test $( git rev-parse --short branch1 ) 2 2

check_difflame first-commit test $( git rev-parse --short branch2 ) 0 5

check_difflame first-commit test $( git rev-parse --short test~2 ) 3 0

check_difflame first-commit test $( git rev-parse --short test~3 ) 0 10

check_difflame first-commit test $( git rev-parse --short test~4 ) 2 2

echo everything is ok
