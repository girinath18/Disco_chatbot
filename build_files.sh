#!/bin/bash

echo "BUILD START"

# Install the required dependencies from requirements.txt
python3.9 -m pip install -r requirements.txt

# Run the Django collectstatic command to collect static files
python3.9 manage.py collectstatic --noinput --clear

echo "BUILD END"
