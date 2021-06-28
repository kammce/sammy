#!/usr/bin/env python3

# Standard libraries
import os
import shutil
import time
from pathlib import Path, PurePath

# External dependencies
import click
import requests
from tqdm import tqdm
from git import Repo, Git, RemoteProgress


CHECK_MARK = '\u001b[32m\N{check mark}\u001b[0m'
CROSS_MARK = '\u001b[31m\N{cross mark}\u001b[0m'

SJSU_DEV2_URL = 'https://github.com/SJSU-Dev2'
LIBCORE_URL = f'f{SJSU_DEV2_URL}/liblpc40xx.git'
ARM_TOOLCHAIN_URL = f'{SJSU_DEV2_URL}/gcc-arm-none-eabi-nano-exceptions.git'


class CloneProgress(RemoteProgress):
  def __init__(self):
    super().__init__()
    self.pbar = tqdm()

  def update(self, op_code, cur_count, max_count=None, message=''):
    self.pbar.total = max_count
    self.pbar.n = cur_count
    self.pbar.refresh()
    if max_count == cur_count:
      print("", flush=True)


def GenerateAndCheck(start_message, command_string, error_message):
  click.echo(click.style(start_message, bold=True), nl=False)
  exit_code = os.system(command_string.replace('\n', ' '))
  if exit_code != 0:
    print(CROSS_MARK, flush=True)
    raise Exception(error_message)
  click.echo(CHECK_MARK)


# Set the directory you want to start from
def FileUpsearch(file_name, starting_position):
  # Dir from where search starts can be replaced with any path
  # cur_dir = os.getcwd()
  #
  cur_dir = Path(starting_position).parent.resolve()

  while True:
    file_list = os.listdir(cur_dir)
    parent_dir = os.path.dirname(cur_dir)
    if file_name in file_list:
      return cur_dir
    else:
      if cur_dir == parent_dir:  # if dir is root dir
        raise Exception(f"Could not find {file_name} directory")
      else:
        cur_dir = parent_dir


@click.group()
def main():
  """
  Sammy is a tool for managing SJSU-Dev2 firmware projects and to install
  external packages such as platforms and libraries.
  """
  pass


@main.group()
def project():
  """
  Start and configure firmware projects
  """
  pass


@project.command()
def init():
  """
  Make the current directory into a SJSU-Dev2 project
  """
  Path('.sj2').mkdir(exist_ok=True)
  Path('.sj2/reserved').touch(exist_ok=True)
  Path('library').mkdir(exist_ok=True)
  Path('packages').mkdir(exist_ok=True)


@project.command()
@click.pass_context
@click.argument('project_name', type=click.Path(exists=False))
def start(context, project_name):
  """
  Start a new firmware project.
  """

  Path(project_name).mkdir()

  Path(f'{project_name}/.sj2').mkdir(exist_ok=True)
  Path(f'{project_name}/.sj2/reserved').touch(exist_ok=True)
  Path(f'{project_name}/library').mkdir(exist_ok=True)
  Path(f'{project_name}/packages').mkdir(exist_ok=True)

  os.chdir(project_name)

  context.invoke(install, library="libcore", tag="main")
  context.invoke(install, library="gcc-arm-none-eabi-nano-exceptions",
                 tag="gcc10-2020-q2-preview")


@project.command()
@click.argument('library')
@click.option('--tag', '-t', type=str, default='main')
def install(library, tag):
  """
  Download and install library to project
  """

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', '.')
  except:
    click.secho(f"Could not find a SJSU-Dev2 project!", fg="red")
    return

  sj2_repo_info = requests.get('https://api.github.com/orgs/SJSU-Dev2/repos',
                               params={'per_page': 500}).json()
  sj2_repo_list = [x['name'] for x in sj2_repo_info]
  if library in sj2_repo_list:
    click.secho(f'Downloading {library}...', fg='white', bold=True)
    Repo.clone_from(f'{SJSU_DEV2_URL}/{library}.git',
                    f'{PROJECT_DIRECTORY}/packages/{library}', branch=tag,
                    progress=CloneProgress())
    time.sleep(0.1)
    click.secho(f'Linking {library}...', fg='white', bold=True)
    Path(f'{PROJECT_DIRECTORY}/library/{library}').unlink(missing_ok=True)
    Path(f'{PROJECT_DIRECTORY}/library/{library}').symlink_to(
        f'{PROJECT_DIRECTORY}/packages/{library}/{library}')
  else:
    click.secho(
        f'Could not find "{library}" in SJSU-Dev2 repos list!',
        fg='red')
    click.secho(
        "Installing non-SJSU-Dev2 libraries is currently not supported!",
        fg="red")


@project.command()
@click.argument('library')
def remove(library):
  """
  Delete library from project
  """

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', '.')
  except:
    click.secho(f"Could not find a SJSU-Dev2 project!", fg="red")
    return

  Path(f'{PROJECT_DIRECTORY}/library/{library}').unlink(missing_ok=True)
  shutil.rmtree(f'{PROJECT_DIRECTORY}/packages/{library}/')


@main.command()
@click.argument('test_source_code', type=click.Path(exists=True))
@click.option('--compiler', '-c', default='g++-10', type=str, show_default=True)
@click.option('--run', '-r', is_flag=True)
def build_test(test_source_code, compiler, run):
  """
  Build Test Executable
  """

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', test_source_code)
  except:
    click.echo(
        click.style(
            f"{test_source_code} does not exist within a SJSU-Dev2 project!",
            fg="red"))
    return

  SOURCE_FILE = test_source_code
  SOURCE_FILE_BASENAME = PurePath(SOURCE_FILE).name
  SOURCE_FILE_PARENT_ABSOLUTE = Path(SOURCE_FILE).parent.resolve()
  RELATIVE_PATH_FROM_PROJECT = PurePath(
      SOURCE_FILE_PARENT_ABSOLUTE).relative_to(PROJECT_DIRECTORY)
  BUILD_DIRECTORY = f'{PROJECT_DIRECTORY}/build/test'
  TEST_EXECUTABLE = (f'{BUILD_DIRECTORY}/{RELATIVE_PATH_FROM_PROJECT}/' +
                     f'{SOURCE_FILE_BASENAME}')

  BUILD_COMMAND = (f'{compiler} ' +
                   # Coverage and Debug Symbols
                   '-g ' +
                   '--coverage ' +
                   # Functionality
                   '-fPIC ' +
                   '-fexceptions '
                   '-fkeep-inline-functions ' +
                   '-fprofile-arcs ' +
                   '-ftest-coverage ' +
                   '-fdiagnostics-color ' +
                   '-fsanitize=address ' +
                   # Disabled functionality
                   '-fno-inline ' +
                   '-fno-builtin ' +
                   '-fno-inline-small-functions ' +
                   '-fno-default-inline ' +
                   '-fno-elide-constructors ' +
                   '-fno-stack-protector ' +
                   # Warnings
                   '-Wall ' +
                   '-Wno-variadic-macros ' +
                   '-Wshadow ' +
                   '-Wno-main ' +
                   '-Wno-missing-field-initializers ' +
                   '-Wfloat-equal ' +
                   '-Wundef ' +
                   '-Wno-format-nonliteral ' +
                   '-Wdouble-promotion ' +
                   '-Wswitch ' +
                   '-Wnull-dereference ' +
                   '-Wformat=2 ' +
                   # Defines
                   '-D HOST_TEST=1 ' +
                   '-D PLATFORM=host ' +
                   # Standard and optimization level
                   '-O0 ' +
                   '-std=c++20 ' +
                   '-pthread ' +
                   f'-I {PROJECT_DIRECTORY}/library/ ' +
                   # Saves temporary build files in the same location as
                   # executable which prevents the coverage files (.gcda/.gcno)
                   # from appearing in the root of the project
                   '-save-temps=obj ' +
                   # Source files and final executable
                   f'{SOURCE_FILE} -o {TEST_EXECUTABLE}.exe')

  try:
    Path(os.path.dirname(TEST_EXECUTABLE)).mkdir(parents=True, exist_ok=True)
    GenerateAndCheck(f"Building test '{TEST_EXECUTABLE}.exe' ... ",
                     BUILD_COMMAND,
                     "Failed to build application!")
  except:
    return

  if run:
    Path(f'{TEST_EXECUTABLE}.gcda').unlink(missing_ok=True)
    GenerateAndCheck(f'Running \'{TEST_EXECUTABLE}.exe\' ... \n',
                     f'{TEST_EXECUTABLE}.exe',
                     'Failed to build application!')


@main.command()
@click.argument('source', type=click.Path(exists=True), default='main.cpp')
@click.option('--optimization', '-o', default='g', type=str, show_default=True)
@click.option('--platform', '-p', default='lpc40xx', type=str,
              show_default=True)
@click.option('--linker_script', '-l', default='default.ld', type=str,
              show_default=True)
@click.option('--toolchain', '-t', default='gcc-arm-none-eabi-nano-exceptions',
              type=str, show_default=True)
@click.option('--compiler', '-c', default='arm-none-eabi-g++', type=str,
              show_default=True)
def build(source, optimization, platform, linker_script, toolchain, compiler):
  """
  Build Application
  """

  OPTIMIZATION_LEVEL = optimization
  PLATFORM = platform
  LINKER_SCRIPT = linker_script
  SOURCE_FILE = source
  SOURCE_FILE_BASENAME = PurePath(SOURCE_FILE).name

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', source)
  except:
    click.echo(
        click.style(
            f"{source} does not exist within a SJSU-Dev2 project!",
            fg="red"))
    return

  TOOLCHAIN = f'{PROJECT_DIRECTORY}/packages/{toolchain}'
  BUILD_DIRECTORY = f'{PROJECT_DIRECTORY}/build'
  LIBRARY_DIRECTORY = f'{PROJECT_DIRECTORY}/library'
  PLATFORM_GCC_ARGS_PATH = f'{LIBRARY_DIRECTORY}/lib{PLATFORM}/platform/gcc.txt'

  ARTIFACTS_DIRECTORY = f'{BUILD_DIRECTORY}/{PLATFORM}'
  ARTIFACTS_NAME = f'{ARTIFACTS_DIRECTORY}/{PLATFORM}.{SOURCE_FILE_BASENAME}'
  PLATFORM_ARGUMENTS = Path(f'{PLATFORM_GCC_ARGS_PATH}').read_text()

  BUILD_COMMAND = (f'{TOOLCHAIN}/bin/{compiler} ' +
                   # Functionality
                   f'-fexceptions ' +
                   f'-ffunction-sections ' +
                   f'-fdata-sections ' +
                   f'-fdiagnostics-color ' +
                   # Disabled functionality
                   f'-fno-rtti ' +
                   f'-fno-threadsafe-statics ' +
                   f'-fno-omit-frame-pointer ' +
                   # Warnings
                   f'-Wno-main ' +
                   f'-Wall ' +
                   f'-Wformat=2 ' +
                   f'-Wno-uninitialized ' +
                   f'-Wnull-dereference ' +
                   f'-Wold-style-cast ' +
                   f'-Woverloaded-virtual ' +
                   f'-Wsuggest-override ' +
                   f'-Wno-psabi ' +
                   # Linker Commands
                   f'-Wl,--gc-sections ' +
                   f'-Wl,--print-memory-usage ' +
                   f'--specs=nano.specs ' +
                   f'-T {LIBRARY_DIRECTORY}/lib{PLATFORM}/platform/{LINKER_SCRIPT} ' +
                   # General Compiler Flags
                   f'-g -std=c++20 ' +
                   f'-I {LIBRARY_DIRECTORY} ' +
                   f'-O{OPTIMIZATION_LEVEL} ' +
                   # Defines
                   f'-D PLATFORM={PLATFORM} ' +
                   # Platform specific arguments
                   f'{PLATFORM_ARGUMENTS} ' +
                   f'{LIBRARY_DIRECTORY}/lib{PLATFORM}/platform/startup.cpp ' +
                   f'{SOURCE_FILE} -o {ARTIFACTS_NAME}.elf ' +
                   # IO Redirects to files
                   f'1> {ARTIFACTS_NAME}.size.percent 2> {ARTIFACTS_NAME}.log')

  GENERATE_BINARY = (f'{TOOLCHAIN}/bin/arm-none-eabi-objcopy -O binary ' +
                     f'{ARTIFACTS_NAME}.elf {ARTIFACTS_NAME}.bin')

  GENERATE_HEX = (f'{TOOLCHAIN}/bin/arm-none-eabi-objcopy -O ihex ' +
                  f'{ARTIFACTS_NAME}.elf {ARTIFACTS_NAME}.hex')

  GENERATE_DISASM = (f'{TOOLCHAIN}/bin/arm-none-eabi-objdump ' +
                     f'--disassemble --demangle ' +
                     f'{ARTIFACTS_NAME}.elf > {ARTIFACTS_NAME}.S')

  GENERATE_DISASM_S = (f'{TOOLCHAIN}/bin/arm-none-eabi-objdump ' +
                       f'--all-headers --source --disassemble --demangle ' +
                       f'{ARTIFACTS_NAME}.elf > {ARTIFACTS_NAME}.lst')

  GENERATE_SIZE = (f'{TOOLCHAIN}/bin/arm-none-eabi-size ' +
                   f'{ARTIFACTS_NAME}.elf > {ARTIFACTS_NAME}.size')

  Path(ARTIFACTS_DIRECTORY).mkdir(parents=True, exist_ok=True)

  try:
    GenerateAndCheck(f"Building '{ARTIFACTS_NAME}.elf' ... ",
                     BUILD_COMMAND,
                     "Failed to build application!")
  except:
    print(f'Build command:\n{BUILD_COMMAND}')
    print(Path(f'{ARTIFACTS_NAME}.log').read_text())
    return

  try:
    GenerateAndCheck('Generating: .bin  (binary) ',
                     GENERATE_BINARY,
                     'Failed to generate .bin file')

    GenerateAndCheck('            .hex  (intel HEX file) ',
                     GENERATE_HEX,
                     'Failed to generate .hex file')

    GenerateAndCheck('             .S    (disassembly) ',
                     GENERATE_DISASM,
                     'Failed to generate .S file')

    GenerateAndCheck('            .lst  (disassembly with source code) ',
                     GENERATE_DISASM_S,
                     'Failed to generate .lst file')

    GenerateAndCheck('            .size (size information) ',
                     GENERATE_SIZE,
                     'Failed to generate .size file')
  except Exception as inst:
    print('FAILURE!')
    print(inst)
    return

  print()
  click.echo(click.style('Section Memory Usage', bold=True))
  print(Path(f'{ARTIFACTS_NAME}.size').read_text())
  print(Path(f'{ARTIFACTS_NAME}.size.percent').read_text())

  click.echo(click.style('Build Log Contents:', bold=True))
  print(Path(f'{ARTIFACTS_NAME}.log').read_text())


# Start of the main program
if __name__ == "__main__":
  main()
