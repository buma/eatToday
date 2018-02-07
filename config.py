import math
from database import LocalNutrition
weight = 66 #6:54 20.6 7:42 21.6 63 24.7 66
needed_kcal = 2200
needed_kcal_lunch = 1300
#First number are actual calories of lunch
diff = 0 #  721-500
#Calculated based on 15:00-7:00/2 per 2 hours
needed_kcal_2_hours_till_lunch=(needed_kcal_lunch)/(8/2) 
lunch_kcal=500
if diff > 0:
    needed_kcal_2_hours_after_lunch=(needed_kcal-4*needed_kcal_2_hours_till_lunch-lunch_kcal)/2-(diff*0.4)/2
    needed_kcal_2_hours_till_lunch-=(diff*0.6)/4
else:
    needed_kcal_2_hours_after_lunch=(needed_kcal-4*needed_kcal_2_hours_till_lunch-lunch_kcal)/2

needed_protein = 1.5*weight
needed_protein_lunch= 1300/needed_kcal*needed_protein
lunch_protein = math.ceil(500/2200*needed_protein)
diff = 0 # 56-lunch_protein
needed_protein_2_hours_till_lunch=needed_protein_lunch/(8/2) # needed_kcal_2_hours_till_lunch/needed_kcal*needed_protein
if diff > 0:
    needed_protein_2_hours_after_lunch=(needed_protein-4*needed_protein_2_hours_till_lunch-lunch_protein)/2-(diff*0.4)/2
    needed_protein_2_hours_till_lunch-=(diff*0.6/4)
else:
    needed_protein_2_hours_after_lunch=(needed_protein-4*needed_protein_2_hours_till_lunch-lunch_protein)/2

def display_part(hour, sumpart=None):
    water_factor=(hour-7)/2
    if hour < 17:
        factor=(hour-7)/2
        should_part=LocalNutrition(kcal=-needed_kcal_2_hours_till_lunch*factor,
                protein=-needed_protein_2_hours_till_lunch*factor, 
                water=-300*water_factor)
    elif hour==17:
        should_part=LocalNutrition(kcal=-needed_kcal_2_hours_till_lunch*4-lunch_kcal,
                protein=-needed_protein_2_hours_till_lunch*4-lunch_protein, 
                water=-300*water_factor)
    elif hour>17:
        factor=(hour-17)/2
        kcal = needed_kcal_2_hours_till_lunch*4+lunch_kcal
        kcal += needed_kcal_2_hours_after_lunch*factor

        protein = needed_protein_2_hours_till_lunch*4+lunch_protein
        protein += needed_protein_2_hours_after_lunch*factor
        should_part=LocalNutrition(kcal=-kcal,protein=-protein, 
                water=-300*water_factor)
    #print ("SUM:", hour)
    #print("SUM", "{}".format(sumpart))
    #print("SHOULD", should_part.kcal, should_part.protein)
    #print ("DIF:", hour, ":00", " "*55+"{:diff}".format(should_part+sumpart))
    if sumpart is None:
        return -1*should_part
    else:
        return should_part+sumpart
