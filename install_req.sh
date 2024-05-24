#!/bin/bash

# Read each line from requirements.txt
while IFS= read -r package || [[ -n "$package" ]]; do
    # Attempt to install the package
    pip install "$package"
    # Check if the installation was successful
    if [ $? -ne 0 ]; then
        echo "Failed to install $package, continuing with the next package..."
    fi
done < requirements.txt
