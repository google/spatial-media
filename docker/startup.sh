#!/bin/sh
# Run Gunicorn with the Flask app
# app:app refers to module 'app' and callable 'app'
exec gunicorn app:app -w 2 --threads 2 -b 0.0.0.0:5000
