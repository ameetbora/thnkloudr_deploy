import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    UPLOAD_FOLDER = '/uploads'
    TESTCYCLE_PREFIX = 'TestCycle_'
    TESTITEM_PREFIX = 'Test_'
    DB_NAME = 'thnkloudr.db'
    TRELLO_API = '732cd1515823ba47fcc8e205247339f4'
    TRELLO_TOKEN = 'c02ad17b82de33db85d9f9ddf7b7709fc77b6189ec5d55bca862046268162f98'
    BOARD_ID = '6123f753d95a2c8ce3e6c0dd'
    LIST_ID = '6123f753d95a2c8ce3e6c0de'
