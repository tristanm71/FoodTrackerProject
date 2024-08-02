import csv
from cs50 import SQL

db = SQL("sqlite:///food.db")

#with open("data/food.csv", "r") as file:

    #reader = csv.DictReader(file)
    #for row in reader:
        #id = row["fdc_id"]
        #name = row["description"]

        #db.execute("INSERT INTO food(fdc_id, name) VALUES(?, ?)", id, name)

with open("data/food_nutrient.csv", "r") as file:

    reader = csv.DictReader(file)

    for row in reader:

        if row["nutrient_id"] == "203" or row["nutrient_id"] == "204" or row["nutrient_id"] == "205" or row["nutrient_id"] == "208":
            id = row["fdc_id"]
            nutrient_id = row["nutrient_id"]
            amount = row["amount"]

            db.execute("INSERT INTO nutrients (fdc_id, nutrient_id, amount) VALUES (?, ?, ?)", id, nutrient_id, amount)

