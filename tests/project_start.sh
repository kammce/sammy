#!/bin/bash

# Kill script if any of the commands fail
set -e

## Step 1
# Go to home directory
cd ~

# Start a new project called azer
sammy project start azer
cd ~/azer/

# Build application
make application

## Step 2
# Go to home directory
cd ~

# Start a new project called azer
sammy project start nabeel
cd ~/nabeel/

# Build application
make application

## Step 3
# Go to home directory
cd ~

# Attempt to make the "azer" project and have it fail because the azer project already exists.&t=1127s
if ! (sammy project start azer) ; then
  exit 0
else
  exit 1
fi
