#!/bin/bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 10.0.0.211:8000
