import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    UPLOAD_FOLDER = '/uploads'
    TESTCYCLE_PREFIX = 'TestCycle_'
    TESTITEM_PREFIX = 'Test_'
    DB_NAME = 'thnkloudr.db'
    TRELLO_API = ''
    TRELLO_TOKEN = ''
    BOARD_ID = ''
    LIST_ID = '                                                 '
