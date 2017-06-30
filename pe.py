import itertools
import re
import datetime
import math

nondigit = re.compile("(?P<number>\d+)(?P<desc>\D+)")

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   

import dateutil.rrule
import dateutil.relativedelta

import colorama
colorama.init(autoreset=True)

from database import Item
from connectSettings import connectString

engine = sqlalchemy.create_engine(connectString)

Session = sessionmaker(bind=engine)

session = Session() 

def show_pee(date):
    today = date.date()
    tomorow = (date+dateutil.relativedelta.relativedelta(days=1)).date()
    print (today)
    items = session.query(Item.id, Item.time, Item.description) \
            .filter(Item.time.between(today, tomorow)) \
            .filter(Item.type=="PIPI") \
            .order_by(Item.time)
    prev = None
    first = None
    cnt = 0
    for item in items:
        if prev is not None:
            diff = item.time-prev.time
        else:
            diff = ""
            first = item
        print (item.id, item.time, item.description, diff)
        cnt+=1
        prev = item
    print ("All:", cnt, "last-first", item.time-first.time, "avg:", (item.time-first.time)/cnt)
    print ()


dates = dateutil.rrule.rrule(dateutil.rrule.DAILY,
        dtstart=datetime.datetime(2017,6,5))
for date in dates:
    show_part = set()
    show_pee(date)
#now = datetime.datetime.now()
#yesterday = (now-dateutil.relativedelta.relativedelta(days=1))
#show_pee(yesterday)
