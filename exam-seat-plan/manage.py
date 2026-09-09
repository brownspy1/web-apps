#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
# Optional MariaDB/MySQL patch for local development
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    import MySQLdb
    MySQLdb.version_info = (2, 2, 6, "final", 0)
    MySQLdb.__version__ = "2.2.6"
    try:
        from django.db.backends.mysql.base import DatabaseWrapper
        DatabaseWrapper.check_database_version_supported = lambda self: None
    except Exception:
        pass
    try:
        from django.db.backends.mysql.features import DatabaseFeatures
        DatabaseFeatures.can_return_columns_from_insert = False
    except Exception:
        pass
except ImportError:
    pass


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
