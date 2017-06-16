import csv
import datetime

import dataset

file = "./5_6.csv"
date = "05.06.2017"

file ="./6_6.csv"
date = "06.06.2017"
file ="./7_6.csv"
date = "07.06.2017"
file ="./8_6.csv"
date = "08.06.2017"
file ="./9_6.csv"
date = "09.06.2017"
file ="./10_6.csv"
date = "10.06.2017"
file ="./11_6.csv"
date = "11.06.2017"
file ="./12_6.csv"
date = "12.06.2017"
file ="./13_6.csv"
date = "13.06.2017"
file ="./14_6.csv"
date = "14.06.2017"
file ="./15_6.csv"
date = "15.06.2017"
file ="./16_6.csv"
date = "16.06.2017"
db = dataset.connect('sqlite:////home/mabu/programiranje/eatToday/eat1.db')
table = db["eat"]
keep = set(["time", "type", "description"])
with open(file) as f:
     data = csv.DictReader(f)
     for line_o in data:
         line = {}
         for key in line_o.keys():
             if key in keep:
                 line[key] = line_o[key]
         print (line)
         if not line["description"]:
             line["description"] = None
         else:
             if len(line["description"]) < 3:
                line["description"] = None
         
         if line["type"] == "PIJACA":
             line["type"] = "PIJAČA"

         line["time"] = datetime.datetime.strptime(date+" "+line["time"],
                 "%d.%m.%Y %H:%M")
         print(line)
         #table.insert(line)
