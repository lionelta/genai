#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
USAGE:

from lib.regex_db import RegexDB
db = RegexDB('/path/to/regex.db')

### create table
db.create_table()

### insert rows
db.insert_row('text for column (content)', 'text for column (source)')

### search
rows = db.search('regex_pattern')
for row in rows:
    id, content, source = row
    ... ... ...

### disconnect
db.disconnect()

'''
import sys
import os
import argparse
import logging
import sqlite3
import re

LOGGER = logging.getLogger()

class RegexDB:
    def __init__(self, dbpath=None):
        self.id_col = 'id'
        self.content_col = 'content'
        self.source_col = 'source'
        self.tablename = 'regex'
        if dbpath:
            self.conn = self.connect(dbpath)


    def connect(self, dbpath):
        self.conn = sqlite3.connect(dbpath)
        return self.conn


    def search(self, regex, return_count=3, rows=None):
        if not rows:
            self.get_all_rows()


        ret = []
        for row in rows:
            chunkid, content, source = row
            if re.search(regex, content, re.DOTALL|re.IGNORECASE):
                ret.append(row)
                if len(ret) == return_count:
                    break
        return ret


    def get_all_rows(self):
        c = self.conn.cursor()
        c.execute(f"SELECT * FROM {self.tablename}")
        rows = c.fetchall()
        return rows


    def insert_row(self, content, source):
        c = self.conn.cursor()
        sql = f"""INSERT INTO {self.tablename} ({self.content_col}, {self.source_col}) VALUES (?, ?)"""
        c.execute(sql, (content, source))
        self.conn.commit()


    def create_table(self):
        c = self.conn.cursor()
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.tablename} (
                {self.id_col} INTEGER PRIMARY KEY AUTOINCREMENT,
                {self.content_col} TEXT,
                {self.source_col} TEXT
            )
        """)
        self.conn.commit()

    def print_rows(self, rows):
        for rowid, content, source in rows:
            print(f'id: {rowid}')
            print(f'content: {content}')
            print(f'source: {source}')
            print('==================================================')


    def disconnect(self):
        self.conn.close()


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    db = RegexDB('/p/psg/data/lionelta/icmfaqdb1/regex.db')
    c = db.conn.cursor()
    c.execute("SELECT * FROM regex")
    rows = c.fetchall()
    db.print_rows(rows)
    print('==================================================')
    regex = 'p4passwd'
    rows = db.search(regex)
    db.print_rows(rows)

