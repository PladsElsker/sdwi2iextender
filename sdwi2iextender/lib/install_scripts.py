import launch
import pkg_resources
import subprocess
import re


class sdwi2iextender_version_manager:
    @staticmethod
    def ensure_latest():
        if not is_latest("sdwi2iextender"):
            _, latest = get_package_versions("sdwi2iextender")
            assert latest is not None, "Unable to update sdwi2iextender because the latest version cannot not be found"
            
            launch.run_pip(f"install sdwi2iextender=={latest}", f"sdwi2iextender")


def is_latest(package_name):
    current, latest = get_package_versions(package_name)
    if None in [current, latest]:
        return False

    return pkg_resources.parse_version(current) == pkg_resources.parse_version(latest)


def get_package_versions(package_name):
    try:
        current_version = pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None, None

    command = ["pip", "index", "versions", package_name]
    try:
        output = subprocess.check_output(command)
        lines = output.decode().splitlines()
        if lines:
            latest_version = lines[-1].strip()
        else:
            latest_version = None
    except subprocess.CalledProcessError as e:
        print(f"Error checking latest version: {e}")
        latest_version = None

    return find_version_in_string(current_version), find_version_in_string(latest_version)


def find_version_in_string(text):
    version_pattern = r'\b\d+\.\d+\.\d+\b'
    match = re.search(version_pattern, text)
    if match:
        return match.group(0)
    return None
