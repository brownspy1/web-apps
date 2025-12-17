#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

print(f"DEBUG: Original MySQLdb version: {getattr(MySQLdb, 'version_info', 'None')}")

# Force patch
MySQLdb.version_info = (2, 2, 6, "final", 0)
MySQLdb.__version__ = "2.2.6"

print(f"DEBUG: Patched MySQLdb version: {MySQLdb.version_info}")

# Patch MariaDB version check (User has 10.4, Django wants 10.6)
try:
    from django.db.backends.mysql.base import DatabaseWrapper
    DatabaseWrapper.check_database_version_supported = lambda self: None
    print("DEBUG: Patched DatabaseWrapper check_database_version_supported")
except Exception as e:
    print(f"DEBUG: Failed to patch DatabaseWrapper: {e}")

# Patch DatabaseFeatures to disable RETURNING (since usage of 10.4)
try:
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseFeatures.can_return_columns_from_insert = False
    print("DEBUG: Patched DatabaseFeatures.can_return_columns_from_insert = False")
except Exception as e:
    print(f"DEBUG: Failed to patch DatabaseFeatures: {e}")


def main():
    """Run administrative tasks."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
