# sammy

Sammy is a tool for managing SJSU-Dev2 firmware projects and to install external
packages such as platforms and libraries.

## Quick Start

```bash
# Install sammy tool via PIP
pip install sammy-sjsu-dev2

# Create a project
sammy start new_project

# Enter project
cd new_project

# Build main.cpp source code into .elf, .bin, .hex etc. Default platform is the
# LPC40xx series.
sammy build
```

## Dependencies

* python3.6 and above
* git

## Usage

Run `sammy --help` to get information about how to use sammy and what it can do.
A quick guide on the most common commands for sammy are listed here.

```
Usage: sammy [OPTIONS] COMMAND [ARGS]...

  Sammy is a tool for managing SJSU-Dev2 firmware projects and to install
  external packages such as platforms and libraries.

Options:
  --help  Show this message and exit.

Commands:
  build       Build Application
  build-test  Build Test Executable
  install     Download and install library to project
  list        List libraries available from the SJSU-Dev2 organization
  remove      Delete library from project
  start       Start a new firmware project.
```

## Building Code

Building code is as simple as running `sammy build` in a SJSU-Dev2 directory
with a `main.cpp` in it.

```
$ sammy build --help
Usage: sammy build [OPTIONS] [SOURCE]

  Build Application

Options:
  -o, --optimization TEXT   [default: g]
  -p, --platform TEXT       [default: lpc40xx]
  -l, --linker_script TEXT  [default: default.ld]
  -t, --toolchain TEXT      [default: gcc-arm-none-eabi-picolibc]
  -c, --compiler TEXT       [default: arm-none-eabi-g++]
  --help                    Show this message and exit.
```

## Installing Packages

To install a package you need to specify a library name such as `libesp8266` or
`liblpc40xx`. This will scan SJSU-Dev2 repo list and if it exists will download
the repo to the `packages` directory and link the library to the `library`
directory. If the package you want to install is not apart of the SJSU-Dev2 repo
you can specify a URL to an git project and it will be installed.

```
$ sammy install --help
Usage: sammy install [OPTIONS] LIBRARY

  Download and install library to project

Options:
  -d, --project_directory PATH
  -t, --tag TEXT
```

You can list the SJSU-Dev2 projects by using the following comamnd:

```
sammy list
```

You can uninstall a package by running:

```
sammy remove <package_name>
```

## Build Test Files

You can build host tests programs using `sammy build-test file.test.cpp`. The
extension does not matter, but SJSU-Dev2 follows the `.test.cpp` extension
pattern.

```
Usage: sammy build-test [OPTIONS] TEST_SOURCE_CODE

  Build Test Executable

Options:
  -c, --compiler TEXT  [default: g++-10]
  -r, --run
```

