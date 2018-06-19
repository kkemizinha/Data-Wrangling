"""
   This module creates tables that will be used to retrieve
   queries through SQL commands

   To run this script:
    $ python create_database.py

"""

import pandas as pd
from sqlalchemy import create_engine

chunksize = 1000000
rio_db = create_engine('sqlite:///rio.db')

def create_table(filename, tablename):
    for df in pd.read_csv(filename, chunksize=chunksize, encoding='utf-8', iterator=True):
        df.to_sql(tablename, rio_db, index=False, if_exists="replace")

create_table('nodes.csv', 'nodes')
create_table('nodes_tags.csv', 'nodes_tags')
create_table('ways.csv', 'ways')
create_table('ways_nodes.csv', 'ways_nodes')
create_table('ways_tags.csv', 'ways_tags')
