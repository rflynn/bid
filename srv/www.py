# vim: set ts=4 et:

from datetime import datetime
from flask import Flask, request

import sqlite3

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'Hello from Flask! (%s)' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')

