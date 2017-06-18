import csv
import locale

from connectSettings import connectString                                                                                                                        
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import LocalNutrition, LocalNutritionaliase

locale.setlocale(locale.LC_NUMERIC, "sl_SI.UTF-8")
engine = sqlalchemy.create_engine(connectString)
Session = sessionmaker(bind=engine)
session = Session()

with open("./nutriondata.csv", "r") as f:
    data = csv.DictReader(f)
    for line in data:
        #print (line, line["protein"], locale.atof(line["protein"]))
        ingkey = line["ingkey"]
        del line["ingkey"]
        for key, val in line.items():
            if key != "desc":
                if key == "gramwt1" or key == "gramdsc1":
                    if len(val)==0:
                        line[key]=None
                    elif key == "gramwt1":
                        line[key]=locale.atof(val)
                else:
                    line[key]=locale.atof(val)
        print (line)
        nutri = LocalNutrition(**line)
        session.add(nutri)
        session.flush()
        print(nutri)
        alias = LocalNutritionaliase(ingkey=ingkey, ndbno=nutri.ndbno)
        session.add(alias)
        #session.commit()
        #break
