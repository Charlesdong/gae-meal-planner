#!/usr/bin/python
#-*- coding: utf-8 -*-

''' 
Meal-Planner 

Tracks your plans for what to eat on a weekly base. 

V.0.1 by Marcus Kemper

kemper.mt@googlemail.com 
'''




import webapp2
import jinja2
import os
import datetime
import time

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

# Helper functions and things like that...

actual_day = datetime.date.today()

meal_categories = ("Lust und Laune", "Nudeln", "Fleisch","Reis, Bulgur, Couscous","Suppe",u"Süß")

day_names = {0:"Montag",1:"Dienstag",2:"Mittwoch",3:"Donnerstag",4:"Freitag",5:"Samstag",6:"Sonntag"}

calendar_week = time.strftime("%W",time.struct_time(time.localtime()))

def name_actual_day():
    name = day_names[actual_day.weekday()]
    return name



# Handler class for the template engine

class Handler(webapp2.RequestHandler):
  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)

  def render_str(self, template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

  def render(self, template, **kw):
    self.write(self.render_str(template, **kw))

# Database Model for the meal-planner

class Meal(db.Model):
    name = db.StringProperty(required = True)
    category = db.CategoryProperty(required = True, choices=set(meal_categories))
    ingredients = db.StringProperty(multiline = True)
    reference = db.StringProperty()

class Day(db.Model):
    name = db.StringProperty(required = True, choices=set(["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]))
    date = db.DateProperty()
    calendar_week = db.IntegerProperty()
    meal = db.ReferenceProperty(Meal)

# Meal Handler Classes

class MealAdd(Handler):
    
    def render_addmeal(self,content="", error=""):
        self.render("add_meal.html", content = meal_categories, error = error)

    def get(self):
        content = []
        self.render("add_meal.html",content = meal_categories)

    def post(self):
        name = self.request.get("name")
        category = self.request.get("selection")
        ingredients = self.request.get("ingredients")
        reference = self.request.get("reference")
        
        if name:
            m = Meal(name = name, category = category, ingredients = ingredients, reference = reference)
            m.put()
            self.redirect("/")
        else:
            error = "Bitte Namen angeben!"
            content = meal_categories
            self.render_addmeal(content, error)
       
class MealDel(Handler):
    
    def render_meal(self, _id=""):
        _id = int(_id)
        meal = Meal.get_by_id(_id)

        if meal:
            self.render("del_meal.html", meal = meal)
        else:
            error = "Dieses Gericht ist nicht (mehr) existent!"
            self.render("del_meal.html", meal = None, error=error) 
    
    def get(self, _id):
        self.render_meal(_id = _id)       
    
    def post(self, _id=""):
        _id = int(_id)
        m = Meal.get_by_id(_id)
        m.delete()
        self.redirect("/")

# Day Handler Classes

class DayShow(Handler):

    def get(self):
        self.render("show_day.html")


class MainHandler(Handler):
    def get(self):
        kw = calendar_week
        self.render("index.html",actual_day=kw)

app = webapp2.WSGIApplication([('/', MainHandler),
                            ('/add_meal', MealAdd),
                            ('/del_meal/(\d+)', MealDel)],
                              debug=True)
