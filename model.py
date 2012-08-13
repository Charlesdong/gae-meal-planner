#!/usr/bin/env python
#-*- coding: utf-8 -*-



from google.appengine.ext import db

meal_categories = ("Lust und Laune", "Nudeln", "Kartoffeln", "Fleisch","Reis, Bulgur, Couscous","Suppe",u"Süß")


# Database Model for the meal-planner

class Day(db.Model):
    name = db.StringProperty(required = True, choices=set(["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]))
    date = db.DateProperty()
    meal_name = db.StringProperty()
    meal_key_name = db.StringProperty()
    
class Meal(db.Model):
    name = db.StringProperty(required = True)
    category = db.CategoryProperty(required = True, choices=set(meal_categories))
    ingredients = db.StringProperty(multiline = True)
    reference = db.StringProperty()
    day = db.ListProperty(db.Key)



