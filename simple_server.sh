#!/bin/bash

# Check if Python exists
if command -v python3 &>/dev/null; then
    echo "Starting Python HTTP server on port 5000..."
    python3 upload_server.py
else
    echo "Python 3 not found, falling back to Perl server..."
    echo "Starting Perl HTTP server on port 5000..."
    perl simple_server.pl
fi