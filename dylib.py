import subprocess
from pathlib import Path


def get_dependencies(dylib_path: Path):
    process = subprocess.Popen(
        f'dyld_info -dependents "{dylib_path.absolute()}"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = process.communicate()
    out_str = str(out)
    out_str_split = out_str.split('\\n')

    if err != None:
        raise Exception(f'Caught error using dyld_info: {err}')

    result = []

    for i in out_str_split:
        if i.endswith('.dylib'):
            result.append(i.strip())

    return result


def get_name_from_path(dylib_path: Path):
    dylib_path_stem = dylib_path.stem
    dylib_name = dylib_path_stem.removeprefix('lib')
    return dylib_name


def expand_rpath(path: Path, dylib_path: Path):
    if not isinstance(dylib_path, Path):
        raise Exception('dylib_path needs to be a Path')

    if dylib_path.suffix != '.dylib':
        raise Exception("_expand_rpath expected a dylib")

    # Get the dylib's parent directory
    dylib_parent_path = dylib_path.parents[0]

    # Replace @rpath
    return Path(
        str(path).replace('@rpath', str(dylib_parent_path.absolute())))


def search_for_dylibs(initial_library_names: list, initial_search_paths: list, ignored_paths: list):
    if not isinstance(ignored_paths, list):
        raise Exception('ignored_paths needs to be a list')

    search_paths = initial_search_paths.copy()
    # List of found libraries (name only, no path or extension)
    found_libraries = []
    # List of already checked libraries (name only, no path or extension)
    checked_libraries = []
    # Result array [(name, path), (name, path), ...]
    result = []

    def find_dylib(library_name: str):
        for search_path in search_paths:
            resolved_dylib_path = Path(
                search_path, f'lib{library_name}.dylib').resolve()

            # Check if the path should be ignored
            should_ignore = False
            for ignored_path in ignored_paths:
                if resolved_dylib_path.match(ignored_path):
                    should_ignore = True
                    break

            if should_ignore:
                continue

            # Make sure the path exists
            if not resolved_dylib_path.exists():
                continue

            return resolved_dylib_path

    def perform_search(library_names: list):
        for library_name in library_names:
            # Make sure the library hasn't already been found
            if library_name in found_libraries:
                print(f'skipping already known library {library_name}')
                continue

            # Find the top-level library
            found_dylib_path = find_dylib(library_name)
            if found_dylib_path == None:
                print(f"couldn't find dylib for {library_name}")
                continue

            result.append((library_name, found_dylib_path))
            print(f'found dylib for {library_name} [path {found_dylib_path}]')

            # Find dependencies of the top-level library
            dependency_names = []
            for dependency_path in get_dependencies(found_dylib_path):
                expanded_dependency_path = expand_rpath(
                    dependency_path, found_dylib_path)

                dependency_name = get_name_from_path(expanded_dependency_path)
                if dependency_name in checked_libraries:
                    continue

                checked_libraries.append(dependency_name)

                if not dependency_name in dependency_names:
                    dependency_names.append(dependency_name)
                    print(f'adding dependency name {dependency_name}')

                dependency_directory_path = expanded_dependency_path.parents[0]
                if not dependency_directory_path in search_paths:
                    search_paths.append(dependency_directory_path)
                    print(
                        f'adding dependency search path {dependency_directory_path}')

            # Search for dependencies
            perform_search(dependency_names)

    perform_search(initial_library_names)
    return result
