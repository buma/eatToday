from threading import Timer, Thread, Event
import itertools
import notify2
import threading
import datetime
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import func
from sqlalchemy.exc import DBAPIError   
from sqlalchemy.orm import joinedload

import dateutil.rrule
import dateutil.relativedelta

from database import Item, FoodNutrition, LocalNutrition
from connectSettings import creator

engine = sqlalchemy.create_engine('sqlite://', creator=creator)

Session = scoped_session(sessionmaker(bind=engine))

session = Session 
from config import display_part

for hour in range(7,22):
    fn =display_part(hour)
    print ("HOUR: {} kcal:{} protein:{} water:{}".format(hour, fn.kcal,
        fn.protein, fn.water))
fn =display_part(hour)
print ("HOUR: {} kcal:{} protein:{} water:{}".format(hour, fn.kcal,
    fn.protein, fn.water))

notify2.init("EatTime")


def notify(ln, txt):
    print ("{}\n{}".format(txt, ln))
    #return
    n= notify2.Notification("EatTime",
            "{}\n{}".format(txt, ln))

    n.show()

def get_sum(session, start, end=None):
    #print ("ID:", threading.get_ident())
    if end is None:
        end = datetime.datetime.now()
    item = session.query(
            func.sum(FoodNutrition.kcal).label("kcal"),
            func.sum(FoodNutrition.protein).label("protein"),
            func.sum(FoodNutrition.water).label("water")) \
                    .join(Item) \
            .filter(Item.time.between(start, end)) \
            .filter(Item.calc_nutrition != None) \
            .group_by(func.strftime("%Y-%m-%d", Item.time)) \
            .one()
    #print (items)
    print ("{} - {}".format(start,end))
    ln = LocalNutrition(kcal=item.kcal, protein=item.protein, water=item.water)
    print("UNTIL NOW:",ln)
    mins = end.minute
    #print ("{0}:{1} {1}/60 = {2}".format(end.hour, end.minute, end.minute/60))
    hour = end.minute/60+end.hour
    diff = display_part(hour, ln)
    #print (display_part(hour))
    print ("DIFF:", diff)
    rets = []
    if diff.water <= -250:
        rets.append((diff, 0, "PIJ VODO", end))

    if diff.kcal <= -300:
        txt = "JEJ V NASLEDNJE POL URE"
        if diff.kcal <= 5:
            txt = "JEJ BELJAKOVINE V NASLEDNJE POL URE"
        rets.append((diff, 1, txt, end))
    return rets
    #session.remove()

today = datetime.datetime.now().date()
#get_sum(session, today)
nt = datetime.datetime(2018,2,7,9)

class SessionThread(Thread):
    def __init__(self, event, session, diff):
        Thread.__init__(self)
        self.stopped = event
        self.session = session
        self.cnts = 1
        self.diff = diff
        self.test = False

    def call_func(self):
        if self.test:
            end = nt+dateutil.relativedelta.relativedelta(
                    minutes=5*self.cnts)
        else:
            end = datetime.datetime.now()
        print ("NOW:", end)
        end1 = end + dateutil.relativedelta.relativedelta(
                minutes=7)
        rets = get_sum(self.session, today, end1)
        end1 = end + dateutil.relativedelta.relativedelta(
                minutes=35)
        rets += get_sum(self.session, today, end1)
        rets = sorted(rets, key=lambda x: (x[1], x[3]))
        ln = None
        txt = []
        print ("RETS:", rets)
        for type, items in itertools.groupby(rets, key=lambda x: x[1]):
            l = list(items)
            if ln is not None:
                ln = l[0][0]
            txt.append(l[0][2])
        if txt:
            notify(ln, " IN ".join(txt))

    def run(self):
        self.call_func()
        while not self.stopped.wait(0.5 if self.test else self.diff*60):
        #while not self.stopped.wait(5):
            self.call_func()

            if self.test:
                self.cnts+=1

#t = Timer(2, get_sum, args=[Session, today, nt])
#t.start()
#get_sum(session, today, nt)

stopFlag = Event()
#t = SessionThread(stopFlag, Session, 7)

te = SessionThread(stopFlag, Session, 7)
te.start()
#stopFlag.set()
