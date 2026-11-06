#!/bin/bash
# Exit on error
set -e
CURRENT_DIR=$(dirname "$(realpath "$0")")
# Ensure the correct python version is available

# Variable to store the path of the supported Python version
SUPPORTED_PYTHON=""

is_venv_activated() {
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Not in a virtual environment."
        return 1
    else
        echo "In a virtual environment: $VIRTUAL_ENV"
        return 0
    fi
}

# Function to check if python3 command is available
check_python3_command() {
    if command -v python3 &>/dev/null; then
        echo "python3 command is available."
        return 0
    else
        echo "python3 command is not available."
        return 1
    fi
}

# Function to check Python version
check_python_version() {
    local version
    version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

    if [[ "$version" == "3.11" || "$version" == "3.12" || "$version" == "3.13" || "$version" == "3.14" || "$version" == "3.15" ]]; then
        echo "Python version $version is installed."
        SUPPORTED_PYTHON="python${version}"
        return 0
    else
        echo "Python version $version is not supported. Installing Python 3.12..."
        return 1
    fi
}

# Function to install Python 3.12
install_python3_12() {
    # Add the deadsnakes PPA for newer Python versions
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install python3.12 -y

    # Verify installation
    if python3.12 --version; then
        echo "Python 3.12 installed successfully."
        SUPPORTED_PYTHON=$(which python3.12)
    else
        echo "Failed to install Python 3.12."
        exit 1
    fi
}

# Check if a venv is activated
if is_venv_activated; then
  echo "[ERROR] You are already in a virtual environment. If this venv is in the Puma Root, make sure the venv runs
  python3.11-3.15 and make sure you have run pip install -r requirements.
  If this is another virtual environment, please execute $0 again outside this venv."
  exit 1
fi

#Do the actual python checks
if check_python3_command; then
    if ! check_python_version; then
        install_python3_12
    fi
else
    echo "Installing Python 3.12 as python3 command is not available..."
    install_python3_12
fi

# Verify that SUPPORTED_PYTHON is set
if [[ -z "$SUPPORTED_PYTHON" ]]; then
    echo "Error: No supported Python version found."
    exit 1
fi

# Go to puma dir
PUMA_ROOT="$CURRENT_DIR/../.."
cd "$PUMA_ROOT"

# We can now use $SUPPORTED_PYTHON to run commands with the supported Python version
echo "Setting up a virtual environment..."
sudo apt install "$SUPPORTED_PYTHON-venv"
sudo apt install python3-pip
$SUPPORTED_PYTHON -m venv venv
chmod 777 ./venv/bin/activate

source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Puma setup completed"
