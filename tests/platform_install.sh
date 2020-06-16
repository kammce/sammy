#!/bin/bash

# Kill script if any of the commands fail
set -e

# Download and setup SJSU-Dev2 platform
sammy platform install

# Enter the hello world project
cd ~/SJSU-Dev2/projects/hello_world

# Attempt to build the project
make application
