import sqlite3
#connectString = "mysql+oursql://mabuF:|_|nterberger@localhost/filmi"
db_path = '/home/mabu/programiranje/eatToday/eat1.db'
connectString = 'sqlite:///' + db_path
creator = lambda: sqlite3.connect('file:{}?mode=ro'.format(db_path), uri=True)
