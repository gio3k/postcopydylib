from argparse import ArgumentParser
import os
from pathlib import Path
import shutil
from .dylib import search_for_dylibs
from .xcode import load_build_config

# Parse arguments
parser = ArgumentParser(description='XcodePostRunPath')
parser.add_argument('-t', '--target-name',
                    help='Target name', required=True)
parser.add_argument('-c', '--configuration-name',
                    help='Configuration name', required=True)
parser.add_argument(
    '-o', '--output-path', help='Library output directory location', required=True, dest='output_path')
parser.add_argument('-p', '--project-path',
                    help='Path to the .xcodeproj or .pbxproj', required=True, dest='project_path')
#parser.add_argument('-e', '--executable-path',
                    #help='Target executable', required=True)
args = parser.parse_args()


build_config = load_build_config(
    args.project_path, args.target_name, args.configuration_name)


dylibs = search_for_dylibs(build_config.get_linked_libraries(
), build_config.get_library_search_paths(), ['/usr/lib/*'])

# Check for output directory
clean_output_path = Path(args.output_path).expanduser().resolve()
print('checking for output directory...')
if clean_output_path.exists():
    print('found output path!')
else:
    print(f'creating output directory @ {clean_output_path}')
    try:
        os.mkdir(clean_output_path)
    except:
        print(f'failed to create output directory')
        exit(1)
    print(f'created')

# Copy dylibs
for dylib_name, dylib_path in dylibs:
    # Check if the library already exists there
    dylib_output_path = clean_output_path / f'lib{dylib_name}.dylib'
    if dylib_output_path.exists():
        print(f'overwriting old dylib for {dylib_name}...')
        os.remove(dylib_output_path)

    # Copy library
    shutil.copy(dylib_path, dylib_output_path)
    print(f'copied {dylib_name} to {dylib_output_path}')
