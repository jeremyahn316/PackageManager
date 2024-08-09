# Package Manager

## Overview

This Package Manager is a Python-based tool designed to mimic the basic functionalities of package managers such as npm. It allows users to initialize simple projects and add packages and its dependencies for Node.js projects.

## Features

- Initialize a new project with a `package.json` file
- Add dependencies to your project
- Install packages and their dependencies
- Detect and prevent circular dependencies
- Track installed packages in a `node_modules.json` file

## Requirements

- Python 3.x
- `requests` library

## Installation

1. Clone this repository or download the `main.py` and `requirement.txt` file.
2. Install the required `requests` library in `requirement.txt` file : pip install -r `requirements.txt`

## Usage

### Initializing a Project

To create a new `package.json` file for your project:

python `main.py` init

You will be prompted to enter project details such as name, version, description, author, and license.

### Adding a Dependency

To add a new dependency to your project:

python main.py add <package_name>[@<version>]

Example: 

python main.py add express@4.17.1

If no version is specified, it will default to "latest".

### Installing Dependencies

To install all dependencies listed in your `package.json` file:

python main.py install 

This command will download and install all specified packages and their dependencies into a `node_modules` directory.

## How It Works

- The tool uses the npm registry (https://registry.npmjs.org) to fetch package information and download tarballs.
- Dependencies are tracked in the `package.json` file.
- Installed packages are recorded in a `node_modules.json` file to prevent redundant downloads.
- The tool checks for and prevents circular dependencies during installation.

## Limitations

- This is a simplified version of a package manager and may not include all features of full-fledged package managers like npm.
- Only supports functionality such as init, add, and install
- Version parsing for package installation is not robust; not able to read range or URL API endpoints



