import pymysql

pymysql.install_as_MySQLdb()

# Monkey patch version for Django 5/6 compatibility
import MySQLdb
if not hasattr(MySQLdb, 'version_info'):
    setattr(MySQLdb, 'version_info', (2, 2, 6, "final", 0))
if not hasattr(MySQLdb, '__version__'):
    setattr(MySQLdb, '__version__', "2.2.6")
