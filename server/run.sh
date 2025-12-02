#!/bin/bash
# Script to run the BiblioScan server with Python 3.11

cd "$(dirname "$0")"

# Activate mise and use Python 3.11
eval "$(mise activate)"

# Activate virtual environment
source venv/bin/activate

# Run the server
python server.py


