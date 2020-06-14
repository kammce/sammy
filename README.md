# sammy

Sammy is a tool for managing SJSU-Dev2 firmware projects and to install external
packages such as platforms and libraries.

## Quick Start

```bash
# Install sammy tool
pip install sammy-sjsu-dev2

# Install SJSU-Dev2
sammy platform install

# Create a new project where "my_project" can be any valid folder name
sammy project start my_project
```

## Dependencies

* python3.6 and above

## Installation

```bash
pip3 install sammy-sjsu-dev2
```

or

```bash
python3 -m pip install sammy-sjsu-dev2
```

or, if pip already points to the python3 version simply run:

```bash
pip install sammy-sjsu-dev2
```

## Usage

Run `sammy --help` to get information about how to use sammy and what it can do.
A quick guide on the most common commands for sammy are listed here.

### Installing SJSU-Dev2

The easiest way to install SJSU-Dev2 is to do it the automated way via `sammy`.

```bash
sammy platform install
```

### Updating SJSU-Dev2

In order update SJSU-Dev2 to its latest version as it appears on its master
branch on github, run:

```bash
sammy platform update
```

NOTE: That you do not need to specify where SJSU-Dev2 is. If it is installed,
then this command will find it. This is done by looking at the
`~/.sjsu_dev2.mk` which is generated after a successful installation of
SJSU-Dev2.

### Creating a New Firmware Project

SJSU-Dev2 projects can be created anywhere on your computer. This command
creates a folder with the contents of the starter project inside of it.

```bash
sammy project start my_project
```

Change `my_project` to whatever name you'd like your project to be.
