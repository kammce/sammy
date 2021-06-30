#!/usr/bin/env python3

# Standard libraries
import os
import shutil
from pathlib import Path, PurePath

# External dependencies
import click
import requests
import giturlparse


CHECK_MARK = '\u001b[32m\N{white heavy check mark}\u001b[0m'
CROSS_MARK = '\u001b[31m\N{cross mark}\u001b[0m'

SJSU_DEV2_URL = 'https://github.com/SJSU-Dev2'
LIBCORE_URL = f'f{SJSU_DEV2_URL}/liblpc40xx.git'
ARM_TOOLCHAIN_URL = f'{SJSU_DEV2_URL}/gcc-arm-none-eabi-nano-exceptions.git'

BASIC_MAIN_CPP = """
# include <libcore/utility/log.hpp>

int main()
{
  for (int i = 0; i < 15; i++)
  {
    sjsu::log::Print("Hello World!\\n");
    sjsu::Delay(1s);
  }

  return 0;
}
"""


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
  if Path(starting_position).is_dir():
    cur_dir = Path(starting_position).absolute()
  else:
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


def GetListOfSJSUDev2Repos():
  sj2_repo_info = requests.get('https://api.github.com/orgs/SJSU-Dev2/repos',
                               params={'per_page': 500}).json()
  return [x['name'] for x in sj2_repo_info]


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
@click.pass_context
@click.argument('project_name', type=click.Path(exists=False))
def start(context, project_name):
  """
  Start a new firmware project.
  """

  click.secho(f'Creating project: {project_name}', fg='white', bold=True)
  Path(project_name).mkdir()

  click.echo(f'    Creating "{project_name}/.sj2" directory')
  Path(f'{project_name}/.sj2').mkdir(exist_ok=True)
  Path(f'{project_name}/.sj2/reserved').touch(exist_ok=True)

  click.echo(f'    Creating "{project_name}/library" directory')
  Path(f'{project_name}/library').mkdir(exist_ok=True)

  click.echo(f'    Creating "{project_name}/packages" directory')
  Path(f'{project_name}/packages').mkdir(exist_ok=True)

  click.echo(f'    Creating "{project_name}/main.cpp" source file')
  Path(f'{project_name}/main.cpp').write_text(BASIC_MAIN_CPP)

  click.echo("")

  context.invoke(install, library="libcore", tag="main",
                 project_directory=project_name)
  context.invoke(install, library="libarmcortex",
                 tag="main", project_directory=project_name)
  context.invoke(install, library="liblpc40xx", tag="main",
                 project_directory=project_name)
  context.invoke(install, library="libstm32f10x",
                 tag="main", project_directory=project_name)
  context.invoke(install, library="gcc-arm-none-eabi-nano-exceptions",
                 tag="gcc10-2020-q2-preview", project_directory=project_name)


@project.command()
@click.argument('library')
@click.option('--project_directory', '-d', type=click.Path(exists=True),
              default='.')
@click.option('--tag', '-t', type=str, default='main')
def install(library, project_directory, tag):
  """
  Download and install library to project
  """

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', project_directory)
  except:
    click.secho(f"Could not find a SJSU-Dev2 project!", fg="red")
    return

  os.chdir(f'{PROJECT_DIRECTORY}/packages/')

  sj2_repo_list = GetListOfSJSUDev2Repos()

  click.secho(f'Installing library: {library}', fg='white', bold=True)

  if library in sj2_repo_list:
    repo_name = f'{library}'
    clone_command = f'git clone {SJSU_DEV2_URL}/{library}.git --branch {tag}'
  else:
    repo_name = giturlparse.parse(f'{library}').name
    clone_command = f'git clone {library} --branch {tag}'

  exit_code = os.system(clone_command)

  if exit_code == 0:
    library_path = f'{PROJECT_DIRECTORY}/library/{repo_name}'
    package_path = f'{PROJECT_DIRECTORY}/packages/{repo_name}/{repo_name}'

    Path(library_path).unlink(missing_ok=True)

    # If this is a library, then the repo will contain a directory with the
    # same name as the repo. That directory will contain all the source files
    # for the library. Link this to the library directory to give it access to
    # the build system.
    if Path(package_path).exists():
      Path(library_path).symlink_to(package_path)

    click.echo(CHECK_MARK)
  else:
    click.echo(CROSS_MARK)

  click.echo('')


@project.command()
def list():
  click.secho('List of package repos in SJSU-Dev2\n', fg='white', bold=True)
  print('\n'.join(GetListOfSJSUDev2Repos()))


@project.command()
@click.argument('library')
@click.option('--project_directory', '-d', type=click.Path(exists=True),
              default='.')
def remove(library, project_directory):
  """
  Delete library from project
  """

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', project_directory)
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

  try:
    PROJECT_DIRECTORY = FileUpsearch('.sj2', source)
  except:
    click.echo(
        click.style(
            f"{source} does not exist within a SJSU-Dev2 project!",
            fg="red"))
    return

  OPTIMIZATION_LEVEL = optimization
  PLATFORM = platform
  LINKER_SCRIPT = linker_script
  SOURCE_FILE = source
  SOURCE_FILE_BASENAME = PurePath(SOURCE_FILE).name
  SOURCE_FILE_PARENT_ABSOLUTE = Path(SOURCE_FILE).parent.resolve()
  RELATIVE_PATH_FROM_PROJECT = PurePath(
      SOURCE_FILE_PARENT_ABSOLUTE).relative_to(PROJECT_DIRECTORY)

  TOOLCHAIN = f'{PROJECT_DIRECTORY}/packages/{toolchain}'
  BUILD_DIRECTORY = f'{PROJECT_DIRECTORY}/build'
  LIBRARY_DIRECTORY = f'{PROJECT_DIRECTORY}/library'
  PLATFORM_GCC_ARGS_PATH = f'{LIBRARY_DIRECTORY}/lib{PLATFORM}/platform/gcc.txt'

  ARTIFACTS_DIRECTORY = (f'{BUILD_DIRECTORY}/{PLATFORM}/' +
                         f'{RELATIVE_PATH_FROM_PROJECT}')
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
