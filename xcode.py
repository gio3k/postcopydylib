from pbxproj import XcodeProject, XCConfigurationList, XCBuildConfiguration
from pathlib import Path
from .xcode_plist import expand_from_plist


def get_project_containing_folder(project_path: str) -> Path:
    path_object = Path(project_path)
    if path_object.suffix == '.pbxproj':
        # Go up a directory if the path leads to a .pbxproj
        path_object = path_object.parents[0]
    if path_object.suffix != '.xcodeproj':
        # Expect a .xcodeproj
        raise Exception(f'Expected a .xcodeproj, got {path_object}')
    # Move up a directory to the parent of the .xcodeproj
    path_object = path_object.parents[0]
    return path_object.expanduser().absolute()


def get_project_pbx_path(path: str) -> Path:
    path_object = Path(path)
    if path_object.suffix == '.pbxproj':
        return path_object.absolute()
    if path_object.suffix == '.xcodeproj':
        return (path_object / 'project.pbxproj').expanduser().absolute()


class BuildConfig:
    def __init__(self, internal_config_list, src_root: Path):
        self.internal_config_list = internal_config_list
        self.src_root: Path = src_root
        self.library_search_paths = self.get_library_search_paths()
        self.linked_libraries = self.get_linked_libraries()

    def get_linked_libraries(self) -> list:
        result = []
        for bcfg_object in self.internal_config_list:
            flags = bcfg_object.buildSettings['OTHER_LDFLAGS']
            if flags == None:
                continue
            for flag in flags:
                if not flag.startswith('-l'):
                    # Ignore unknown linker flag / non library flag
                    continue
                if flag not in result:
                    result.append(flag.removeprefix('-l'))
        return result

    def get_library_search_paths(self) -> list:
        result = []
        for bcfg_object in self.internal_config_list:
            for v in bcfg_object.buildSettings['LIBRARY_SEARCH_PATHS']:
                # Ignore $(inherited)
                if v == '$(inherited)':
                    continue

                # Expand custom path values
                v = expand_from_plist(v)

                # Create path object
                path = Path(v)

                # Make path relative to the src root if possible
                if not path.is_absolute():
                    path = self.src_root / path

                # Resolve and append
                result.append(path.resolve())
        return result


def load_build_config(project_path: Path, target_name: str, configuration_name: str):
    # Compute path to project
    src_root = get_project_containing_folder(project_path)

    # Open the project
    root_project = XcodeProject.load(get_project_pbx_path(project_path))

    # Get the PBXProject object
    pbx_project_object = root_project.objects.get_objects_in_section('PBXProject')[
        0]
    pbx_project_bcfg_list_id = pbx_project_object.buildConfigurationList

    # Get target build config list
    target_object = root_project.get_target_by_name(target_name)
    if target_object == None:
        raise Exception(f"No target found with name {target_name}")
    target_bcfg_list_id = target_object.buildConfigurationList

    # Get all related build configs
    bcfg_all_list: list[XCBuildConfiguration] = []

    def convert_build_configuration_list(list_id: str) -> list:
        item: XCConfigurationList = root_project.objects[list_id]

        for bcfg_id in item.buildConfigurations:
            bcfg_object = root_project.objects[bcfg_id]

            if bcfg_object.name == configuration_name:
                bcfg_all_list.append(bcfg_object)

    convert_build_configuration_list(pbx_project_bcfg_list_id)
    convert_build_configuration_list(target_bcfg_list_id)

    return BuildConfig(bcfg_all_list, src_root)
