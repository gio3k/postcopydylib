import plistlib
from pathlib import Path

XCODE_PREFERENCE_PLIST_PATH = '~/Library/Preferences/com.apple.dt.Xcode.plist'
_plist_data = None


def _get_plist_data():
    global _plist_data
    if _plist_data != None:
        return _plist_data
    resolved_path = Path(XCODE_PREFERENCE_PLIST_PATH).expanduser().resolve()
    with open(resolved_path, 'rb') as f:
        _plist_data = plistlib.load(f, fmt=plistlib.PlistFormat.FMT_BINARY)
    return _plist_data


def _get_custom_path_data():
    plist_data = _get_plist_data()
    if 'IDEApplicationwideBuildSettings' not in plist_data:
        raise Exception("Failed to read Xcode custom path data")
    return plist_data['IDEApplicationwideBuildSettings']


def get_plist_var(key: str):
    path_data = _get_custom_path_data()
    if key not in path_data:
        raise Exception(f"Couldn't find Xcode custom path with key '{key}'")
    return path_data[key][0]


def expand_from_plist(v: str):
    path_data = _get_custom_path_data()
    result = v
    for k in path_data:
        result = result.replace(f'$({k})', path_data[k][0])
    return result
