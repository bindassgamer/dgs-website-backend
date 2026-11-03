#!/usr/bin/env python
import os
import sys


def main():
    # Select settings by environment: set DJANGO_CONFIGURATION=production on
    # the server; anywhere else this runs the development settings.
    environment = os.environ.get("DJANGO_CONFIGURATION", "development")
    if environment == "production":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
