#!/bin/bash

# Kill script if any of the commands fail
set -e

# Attempt to update, nothing should happen as SJSU-Dev2 is at its latest
sammy platform update

# Go to SJSU-Dev2
cd ~/SJSU-Dev2/

# Revert head of master back two commits
git reset --hard HEAD~2

# Attempt to update again, this time, SJSU-Dev2 should update to the latest
# master
sammy platform update

# Checkout a new branch and dirty the current workspace by making a new file
# and adding it to the commit list.
git checkout -b new-branch
touch new_file
git add new_file

# Attempt to update again, this time, this should fail and prompt the user to
# switch to master to update.
if ! (sammy platform update) ; then
  exit 0
else
  exit 1
fi
