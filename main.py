import argparse
import io
import json
import os
import sys
import tarfile
import requests


PACKAGE_FILE = 'package.json'
NODE_MODULES_FILE = 'node_modules.json'
REGISTRY_URL = 'https://registry.npmjs.org'
LATEST = "latest"
NODE_MODULES_DIR = "node_modules"

def init_package_file(name, version, description, author, license):
    """
    Initialize a new package.json file with basic project information.

    Args:
        name (str): The name of the project.
        version (str): The version of the project.
        description (str): A brief description of the project.
        author (str): The author of the project.
        license (str): The license type for the project.
    """

    if not os.path.exists(PACKAGE_FILE):
        with open(PACKAGE_FILE, 'w') as f:
            init = {"name": name,
                    "version": version,
                    "description": description,
                    "author": author,
                    "license": license} 
            json.dump(init, f, indent=2)    

def init_node_modules_file():
    """
    Initialize a new node_modules.json file if it doesn't exist.
    This file keeps track of installed packages and their versions.
    """

    if not os.path.exists(NODE_MODULES_FILE):
        with open(NODE_MODULES_FILE, "w") as f:
            json.dump({}, f, indent=2)

def add(arg):
    """
    Parse the package argument and add the package name and version as a dependency.

    Args:
        arg (str): The package name, optionally including a version (e.g., 'package@1.0.0').
    """

    package = arg
    version = LATEST

    # If version is specified, add the version 
    if "@" in arg:
        package, version = arg.split('@')
    add_dependency(package, version)

def add_dependency(package, version):
    """
    Add a package dependency and its corresponding version to the package.json file.

    Args:
        package (str): The name of the package to add.
        version (str): The version of the package to add.
    """

    # Not allowing user to add dependencies/package unless package.json has been created
    if not os.path.exists(PACKAGE_FILE):
        print("package.json has not been created, run init command first")
        return
    
    with open(PACKAGE_FILE, 'r') as f:
        package_data = json.load(f)

    # If not dependencies have been added to package.json file
    if 'dependencies' not in package_data:
        package_data['dependencies'] = {}

    # Add the package and its version and key, value pair in dependencies object
    package_data['dependencies'][package] = version

    with open(PACKAGE_FILE, 'w') as f:
        json.dump(package_data, f, indent=2)
    print(f"Added {package}@{version} to {PACKAGE_FILE}")

def install_dependencies():
    """
    Install all dependencies listed in package.json file.
    """

    with open(PACKAGE_FILE, 'r') as f:
        package_data = json.load(f)

    dependencies = package_data.get('dependencies', {})

    # For each package in package.json, install the pacakge and its version
    for package_name, version in dependencies.items():
        print(f"Installing {package_name}@{version}...")
        install_package(package_name, version, set())

def install_package(package_name, version, track):
    """
    Install a specific package with the given version.
    Use track to detect Circular Depedency

    Args:
        package_name (str): The name of the package to install.
        version (str): The version of the package to install.
        track (set): A set of packages names that were installed.
    """

    # If package name has already been installed, there is a circular dependency
    if package_name in track:
        print(f"Circular dependency detected; exiting installation")
        return
    track.add(package_name)
    
    # Not allowing user to install dependencies/package unless package.json has been created
    if not os.path.exists(PACKAGE_FILE):
        print("package.json has not been created, run init command first")
        return

    # Create node module file to keep track of installed packages and their version
    init_node_modules_file()
    with open(NODE_MODULES_FILE, 'r') as f:
        node_modules_data = json.load(f)

    # Check if the package is already installed in node_modules.json
    if package_name in node_modules_data and node_modules_data[package_name] == version:
        print(f"{package_name}@{version} is already installed.")
        # In case we downloaded a package without it dependencies via manual download
        check_subdependencies(package_name, track)
        return
    
    # Update node_modules.json
    node_modules_data[package_name] = version
    with open(NODE_MODULES_FILE, 'w') as f:
        json.dump(node_modules_data, f, indent=2)

    # Remove prefix of version if exists (ie ^ or ~)
    if version[0] in ["~", "^"]:
        version = version[1:]
    
    # Create URL for package and the version and submit API request for corresponding json
    url = f"{REGISTRY_URL}/{package_name}/{version}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Package retrieval for {package_name} for version {version} failed")
        return 
    
    package_info = response.json()
    if version == LATEST:
        version = package_info['version']

    # Retrieve tar file url and submit an API request
    tarball_url = package_info['dist']['tarball']
    response_tar = requests.get(tarball_url)
    if response_tar.status_code != 200:
        print("Package instalation from json has failed")
        return 

    package_dir = os.path.join(NODE_MODULES_DIR, package_name)
    os.makedirs(package_dir, exist_ok=True)

    # Download the package
    with tarfile.open(fileobj=io.BytesIO(response_tar.content), mode="r:gz") as tar:
        tar.extractall(path=package_dir)

    print(f"Installed {package_name}@{version}")


    check_subdependencies(package_name, track)

def check_subdependencies(package_name, track):
    """
    Check and install dependencies of an installed package.

    Args:
        package_name (str): The name of the package to check for subdependencies.
        track (set): A set of packages names that were installed.
    """

    # Check and install dependencies of the installed package
    package_path = f"node_modules/{package_name}/package/package.json"
    if os.path.exists(package_path):
        with open(package_path, 'r') as f:
            package_data = json.load(f)
        sub_dependencies = package_data.get('dependencies', {})
        for sub_package_name, sub_version in sub_dependencies.items():
            install_package(sub_package_name, sub_version, track)

def main():
    parser = argparse.ArgumentParser(description="Simple Package Manager")
    subparser = parser.add_subparsers(dest="command", help="Commands users can use")

    # Init Command
    subparser.add_parser("init", help="Create package.json")

    # Add Command
    add_parser = subparser.add_parser("add", help="Add a dependency to package.json")
    # parser.add_argument("add", required=False, help="Add a dependency to package.json, Package name (and version if applicable)")
    add_parser.add_argument('package', help="Package name (and version if applicable)")

    # Install Command
    subparser.add_parser("install", help="Install all dependencies in package.json")

    args = parser.parse_args()

    if len(sys.argv) < 2:
        print("Enter a command")
        parser.print_help()
    if args.command == "init":
        name = input("Project name: ")
        version = input("Project version: ")
        description = input("Project description: ")
        author = input("Project author: ")
        license = input("License for this project: ")
        init_package_file(name, version, description, author, license)
    elif args.command == "add":
        # TODO
        if len(sys.argv) > 3:
            parser.error('Too many arguments for add command')
        add(args.package)
    elif args.command == "install":
        # TODO
        install_dependencies()
    else:
        print("Enter a valid command")
        parser.print_help()

if __name__ == "__main__":
    main()