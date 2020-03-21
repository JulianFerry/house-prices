from src import database

import os
import pandas as pd
import sqlalchemy as sqla
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy_utils import database_exists


TEST_DIR = os.path.dirname(__file__)

# Clean up previous test files
def _remove_file(f):
    if os.path.exists(f):
        os.remove(f)
for f in [os.path.join(TEST_DIR, 'database.sqlite')]:
    _remove_file(f)


def test_extend_url():

    # Set up: database config
    url = 'sqlite:///'
    db = 'database.sqlite'

    # Expected values
    expected_url = URL(**{
        'drivername': 'sqlite',
        'database': db
    })

    # Test that: the url is created correctly
    assert database._extend_url(url, db) == expected_url


class TestGetConfig():

    def test_get_config_defaults(self):

        # Function call
        default_url, default_db, default_schema = database.get_config()

        # Test that: the default values are loaded
        assert default_url == make_url('mysql+pymysql://root:root@localhost:3306')
        assert default_db == 'HousePrices'
        assert default_schema == 'dev'

    def test_get_config_envs(self):

        # Set up: environment variables
        os.environ['SQL_SERVER_URL'] = custom_url = 'sqlite:///'
        os.environ['SQL_DATABASE'] = custom_db = 'database.sqlite'
        os.environ['SQL_SCHEMA'] = custom_schema = 'build'

        # Function call
        url, db, schema = database.get_config()

        # Test that: the environment variables are loaded
        assert url == make_url(custom_url)
        assert db == custom_db
        assert schema == custom_schema


def test_load():

    # Set up: database config
    url = make_url('sqlite:///')
    db = os.path.join(TEST_DIR, 'database.sqlite')
    schema = 'test'
    table = 'table'

    # Set up: create table inside database
    db_url = 'sqlite:///' + db
    table_name = '_'.join([schema, table])
    engine = sqla.create_engine(db_url)

    engine.execute(
        f'CREATE TABLE "{table_name}" ('
            'id INTEGER NOT NULL,'
            'name VARCHAR, '
            'PRIMARY KEY (id));'
    )
    engine.execute(
        f'INSERT INTO "{table_name}" '
            '(id, name) '
            'VALUES (1,"raw1")'
    )

    # Function call
    data = database.load(url, db, schema, table)

    # Test that: the data is loaded correctly
    assert data.shape == (1, 2)
    assert list(data.columns) == ['id', 'name']
    assert data.values.tolist() == [[1, 'raw1']]

    # Clean up
    _remove_file(db)


def test_save():

    # Set up: database config
    url = make_url('sqlite:///')
    db = os.path.join(TEST_DIR, 'database.sqlite')
    schema = 'test'
    table = 'table'

    # Set up: data to save
    data = pd.DataFrame({
        'id': [1, 2],
        'name': ['raw1', 'raw2']
    })

    # Function call
    database.save(data, url, db, schema, table)

    # Test that: the database exists
    db_url = 'sqlite:///' + db
    assert database_exists(db_url)

    # Test that: the table exists
    table_name = '_'.join([schema, table])
    engine = sqla.create_engine(db_url)
    assert table_name in engine.table_names()

    # Clean up
    _remove_file(db)
