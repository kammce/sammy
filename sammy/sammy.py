#!/usr/bin/env python3

# Standard libraries
import re
import sys
import shutil
import os
import logging
from pathlib import Path
import subprocess
import platform as environment_platform

# External dependencies
import click
import coloredlogs

# Create a logger object.
logger = logging.getLogger(__name__)

# By default the install() function installs a handler on the root logger,
# this means that log messages from your code and log messages from the
# libraries that you use will all show up on the terminal.
coloredlogs.install(level='INFO',
    fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s')


def get_sjsu_dev2_path():
  # Get the user's home directory where the SJSU-Dev2's location file should
  # live
  home_directory = str(Path.home())

  # Open the .sjsu_dev2.mk and read its contents
  root_mk_file = open(f'{home_directory}/.sjsu_dev2.mk', 'r')
  root_mk_contents = root_mk_file.read()

  # Use regex to parse just for the location variable
  m = re.search('SJSU_DEV2_BASE[ ]*= (.*)', root_mk_contents)
  base_path = m.group(1)

  return base_path


@click.group()
def main():
  """
  Sammy is a tool for managing SJSU-Dev2 firmware projects and to install
  external packages such as platforms and libraries.
  """
  pass


@main.group()
def platform():
  """
  Install, update, and configure the SJSU-Dev2 platform settings.
  """
  pass


@platform.command()
def install():
  """
  Install SJSU-Dev2 on your computer.
  """
  try:
    # If SJSU-Dev2 is not installed (location file cannot be found), this will
    # throw an exception, meaning we should proceed.
    # If this is successful, then we must exit as we do not want to overwrite
    # the previous SJSU-Dev2 instance.
    platform_path = get_sjsu_dev2_path()
    platform_exists = os.path.isdir(platform_path)

    if platform_exists:
      sys.exit(f'SJSU-Dev2 is already installed in location "{platform_path}"')

  except FileNotFoundError:
    pass

  operating_system = environment_platform.system()
  logging.info('Checking if GIT is installed...')
  try:
    subprocess.call(["git", "--version"])
  except FileNotFoundError:
    logging.info('Installing GIT...')

    if operating_system == 'Linux':
      subprocess.Popen(['sudo', 'apt', 'install', '-y', 'git'],
                      stdout=sys.stdout,
                      stderr=sys.stderr).communicate()
    elif operating_system == 'Darwin':
      subprocess.Popen(['git', '--version'],
                      stdout=sys.stdout,
                      stderr=sys.stderr).communicate()
    else:
      logging.error('Invalid operating system!')
      sys.exit(1)

  logging.info('GIT Installed!')

  logging.info('Downloading SJSU-Dev2 Repo...')

  # Get the user's home directory where the SJSU-Dev2's location file should
  # live
  home_directory = str(Path.home())

  # Clone SJSU-Dev2 into the home directory
  subprocess.Popen(['git', 'clone',
                    'https://github.com/SJSU-Dev2/SJSU-Dev2.git'],
                   cwd=home_directory,
                   stdout=sys.stdout,
                   stderr=sys.stderr).communicate()

  logging.info('Running SJSU-Dev2 setup...')

  # Run setup for SJSU-Dev2 to download, install and configure the tools needed
  # for SJSU-Dev2.
  subprocess.Popen(['./setup'],
                   cwd=f'{home_directory}/SJSU-Dev2',
                   stdout=sys.stdout,
                   stderr=sys.stderr).communicate()

  logging.info('SJSU-Dev2 has been successfully installed!')

@platform.command()
def update():
  """
  Update SJSU-Dev2 on your computer.

  This works even if you did not install SJSU-Dev2 in the home directory.
  """
  try:
    platform_path = get_sjsu_dev2_path()
  except FileNotFoundError:
    logging.error(('Could not find SJSU-Dev2 location file. Make sure '
                   'SJSU-Dev2 is installed.'))
    sys.exit(1)

  # Returns just the branch name of the current branch being used in SJSU-Dev2
  proc = subprocess.Popen(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                          stdout=subprocess.PIPE,
                          cwd=platform_path)

  current_branch = proc.stdout.read()

  if current_branch != b'master\n':
    logging.error(f'SJSU-Dev2 must be on the master branch to be updated!')
    logging.error(f'>> Current branch is: {current_branch.decode("utf-8")}')
    sys.exit(1)
    return

  logging.info('Updating SJSU-Dev2 ...')

  subprocess.Popen(['git', 'pull', 'origin', 'master'],
                   stdout=sys.stdout,
                   stderr=sys.stderr,
                   cwd=platform_path).communicate()


@platform.command()
def complete_update():
  """
  Will update SJSU-Dev2 and re-run setup, which will handle updating and
  upgrading the necessary tools needed for SJSU-Dev2 project.
  """
  logging.info("Not implemented.")


@main.group()
def project():
  """
  Start and configure firmware projects
  """
  pass


@project.command()
@click.argument('project_name')
def start(project_name):
  """
  Start a new firmware project.
  """
  platform_path = get_sjsu_dev2_path()

  try:
    shutil.copytree(f'{platform_path}/projects/starter/', project_name)
    logging.info(f'Creating firmware project in "{project_name}" directory')
  except FileExistsError:
    logging.error(('Failed to create project, project directory '
                   f'"{project_name}" already exists'))
    sys.exit(1)


@main.command()
def build():
  """
  Build projects firmware
  """
  logging.info("Not implemented.")


# Start of the main program
if __name__ == "__main__":
  main()
