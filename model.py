#!/usr/bin/env python
#-*- coding: utf-8 -*-



from google.appengine.ext import db

meal_categories = ("Lust und Laune", "Nudeln", "Kartoffeln", "Fleisch","Reis, Bulgur, Couscous","Suppe",u"Süß")


# Database Model for the meal-planner

class User(db.Model):
    name = db.StringProperty(required = True)
    lastname = db.StringProperty(required = True)
    email = db.EmailProperty(required = True)
    pwd = db.StringProperty(required = True)
    
    
class Day(db.Model):
    name = db.StringProperty(required = True, choices=set(["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]))
    date = db.DateProperty()
    meal_name = db.StringProperty()
    meal_key_name = db.StringProperty()
    owner = db.ReferenceProperty(User)

class Meal(db.Model):
    name = db.StringProperty(required = True)
    category = db.CategoryProperty(required = True, choices=set(meal_categories))
    ingredients = db.StringProperty(multiline = True)
    reference = db.StringProperty()
    day = db.ListProperty(db.Key)
    owner = db.ReferenceProperty(User)

class Authenticated(db.Model):
    logged_in_at = db.DateTimeProperty(auto_now = True)
    
