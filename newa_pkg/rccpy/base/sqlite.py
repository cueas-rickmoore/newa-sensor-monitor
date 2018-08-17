
import datetime
import os
import sqlite3

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def formatForSql(value):
    if hasattr(value, 'dtype'):
        if value.dtype.kind == 'i': return '%d' % value
        elif value.dtype.kind == 'S': return "'%s'" % value
        elif value.dtype.kind == 'f': return str(value)
    elif isinstance(value, (int,long)): return '%d' % value
    elif isinstance(value, basestring): return "'%s'" % value
    elif isinstance(value, float): return str(value)
    else: return str(value)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SqliteDatabaseManager(object):

    AUTO_COMMITABLE = ('DELETE', 'INSERT', 'UPDATE')

    def __init__(self, database_filepath, auto_commit_rate=100,
                       allow_auto_commit=True):
        self.auto_commit_rate = auto_commit_rate
        self.allow_auto_commit = allow_auto_commit

        self.db_filepath = None
        self.connection = None
        self.connection_cursor = None
        self.num_pending_transactions = 0

        self.connect(database_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createIndexes(self, index_defs, unique=False):
        print index_defs
        for index_def in index_defs:
            self.createIndex(*index_def, unique=unique)

    def createIndex(self, index_name, table_name, columns=None, unique=False):
        print 'index_name', index_name
        print 'table_name', table_name
        print 'columns', columns
        print 'unique', unique
        if unique: tmpl = "CREATE UNIQUE INDEX %s ON %s(%s)" 
        else: tmpl = "CREATE INDEX %s ON %s(%s)"
        if columns is not None:
            if isinstance(columns, (list,tuple)):
                sql = tmpl % (index_name, table_name, ','.join(columns))
            elif isinstance(columns, basestring):
                sql = tmpl % (index_name, table_name, columns)
            else:
                msg = "Invalid type for columns argument : %s"
                raise TypeError, msg % type(columns)
        else:
            sql = tmpl % (index_name, table_name, index_name)
        self.execute(sql)
        self.commit()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createTables(self, table_defs):
        if isinstance(table_defs, (tuple,list)):
            for table_name, column_defs in table_defs:
                self.createTable(table_name, column_defs)
        elif isinstance(table_defs, dict):
            for table_name, column_defs in table_defs.items():
                self.createTable(table_name, column_defs)

    def createTable(self, table_name, column_defs, constraints=None):
        CT = "CREATE TABLE %s(%s)"
        FK = "FOREIGN KEY(%s) REFERENCES %s(%s)"
        columns = [ ]
        foreign = [ ]
        for column in column_defs:
            if len(column) == 2:
                columns.append('%s %s' % column)
            elif len(column) == 3:
                columns.append('%s %s' % column[:2])
                foreign.append(FK % (column[0], column[2][0], column[2][1]))
        columns = ', '.join(columns)
        if foreign: columns = '%s, %s' % (columns, ', '.join(foreign))
        if constraints is None: sql = CT % (table_name, columns)
        else: sql = CT % (table_name, '%s, %s' % (columns, constraints))
        self.execute(sql)
        self.commit()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addRecord(self, table_name, column_data):
        WHY = "'column_data' arg  must contain an entry for EVERY column in the table"
        column_names = self.listColumns(table_name,None)
        if column_names is None:
            raise ValueError, "Unrecognized table name '%s'" % table_name

        elif isinstance(column_data, (tuple,list)):
            values = tuple(column_data)
        elif isinstance(column_data, dict):
            values = [ ]
            try:
                for column_name in column_names:
                    values.append(column_data[column_name])
            except KeyError:
                errmsg = 'INSERT failed for %s : %s column data is missing\n%s'
                raise ValueError, errmsg % (table_name, column_name, WHY)
        if len(values) < len(column_names):
            raise ValueError, 'INSERT failed for %s : %s' % (table_name, WHY)

        qms = ',?' * (len(values) -1)
        sql = "INSERT INTO %s VALUES (?%s)" % (table_name, qms)
        self.execute(sql, values)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteRecord(self, table_name, key, key_value):
        DR = "DELETE FROM %s WHERE %s = %s"
        sql = DR % (table_name, key, formatForSql(key_value))
        self.execute(sql)
        self.commit()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, table_name, columns='*', constraints=None,
                      fetch_all=True):
        SEL = "SELECT %s FROM %s" % (columns, table_name)
        if isinstance(columns, basestring):
            sql = SEL % (columns, table_name)
        elif isinstance(columns, (tuple,list)):
            sql = SEL % (','.join(columns), table_name)
        else:
            raise ValueError, "Invalid value for 'columns' argument."

        if constraints is not None: sql = "%s %s" % (sql, constraints)

        return self.fetch(sql, fetch_all)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateRecord(self, table_name, key, key_value, column_data,):
        UPR = "UPDATE OR ROLLBACK SET %s %s WHERE %s=%s"
        updates = [ ]
        for name, value in column_data:
            updates.append('%s=%s' % (name, formatForSql(value)))
        sql = UPR % (table_name, ','.join(updates), key, key_value)
        self.execute(sql)
        self.commit()

    def updateColumn(self, table_name, key, key_value, column_name,
                           new_value, commit=True):
        UPC = "UPDATE %s SET %s=%s WHERE %s=%s"
        sql = UPC % (table_name, column_name, new_value, key,
                     formatForSql(key_value))
        self.autoexec(sql)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def columnExists(self, table_name, column_name):
        return column_name in self.listColumns()

    def indexExists(self, index_name):
        return index_name in self.listIndexes()

    def listColumns(self, table_name):
        result = self.fetch("PRAGMA TABLE_INFO(%s)" % table_name)
        return tuple([column[1] for column in result])

    def listIndexes(self):
        sql = "SELECT name FROM sqlite_master WHERE type='index'"
        return tuple([item[0] for item in self.fetch(sql)])

    def listTables(self, force_fetch=False):
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        return tuple([item[0] for item in self.fetch(sql)])

    def tableExists(self, table_name):
        return table_name in self.listTables()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def autoexec(self, sql, values=None):
        result = self.execute(sql, values)
        if not self.allow_auto_commit:
            return result
        blank = sql.find(' ')
        if sql[:blank] in self.AUTO_COMMITABLE:
            self.num_pending_transactions += 1
            if self.num_pending_transactions >= self.auto_commit_rate:
                self.commit()
        elif sql[:blank] not in ('SELECT','PRAGMA'):
            errmsg = "'%s' SQL statement is not supported for auto commit."
            raise SyntaxError, errmsg % sql[:blank]
        return result

    def closeConnection(self):
        if self.connection is not None:
            if self.num_pending_transactions > 0:
                self.connection.commit()
            self.connection.close()
            self.connection = None
            self.connection_cursor = None
    disconnect = closeConnection

    def closeCursor(self):
        self.connection_cursor.close()
        self.connection_cursor = None

    def commit(self):
        self.connection.commit()
        self.num_pending_transactions = 0

    def connect(self, database_filepath=None):
        self.closeConnection()

        if database_filepath is not None:
            db_filepath = os.path.normpath(os.path.abspath(database_filepath))
        else:
            db_filepath = self.db_filepath
        exists = os.path.exists(db_filepath)

        self.connection = sqlite3.connect(db_filepath)
        self.db_filepath = db_filepath

    def cursor(self):
        if self.connection is None: self.connect()
        if self.connection_cursor is None:
            self.connection_cursor = self.connection.cursor()
        return self.connection_cursor

    def execute(self, sql, values=None):
        cursor = self.cursor()
        if values is None:
            try:
                return cursor.execute(sql)
            except Exception as e:
                print 'SQL ERROR :', sql
                raise
        else:
            try:
                return cursor.execute(sql, values)
            except Exception as e:
                print 'SQL ERROR :', sql
                print 'Values =', values
                raise

    def fetch(self, sql, fetch_all=True):
        cursor = self.cursor()
        if fetch_all: return cursor.execute(sql).fetchall()
        else: return cursor.execute(sql)

