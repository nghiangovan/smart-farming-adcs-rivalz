#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Check if virtualenv is installed, if not, install it
if ! python3 -m pip show virtualenv > /dev/null 2>&1; then
    echo "virtualenv not found, installing..."
    python3 -m pip install --user virtualenv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "../.venv" ]; then
    python3 -m virtualenv ../.venv
    echo "Virtual environment '../.venv' created."
else
    echo "Virtual environment '../.venv' already exists."
fi

# Activate the virtual environment
source ../.venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing project dependencies..."
pip install -r requirements.txt

# Function to install packages and update requirements.txt
install_and_update_requirements() {
    pip install "$@"
    for package in "$@"
    do
        pip freeze | grep "^$package==" >> requirements.txt
    done
}

# Example usage: Install new packages and update requirements.txt
install_and_update_requirements langchain langchain-openai

echo ""
echo "✅ Environment setup complete. Virtual environment '../.venv' is ready to use."
echo ""
echo " Please set your OPENROUTER_API_KEY environment variable before running the application."
echo "   You can create a '.env' file in the providers directory with the following content:"
echo "   OPENROUTER_API_KEY=your-openrouter-api-key"
echo ""
echo "➡️  Remember to activate the virtual environment with 'source ../.venv/bin/activate' before running your scripts."
echo ""

# Deactivate virtual environment (optional)
# deactivate 