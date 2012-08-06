#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import datetime

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)



meal_categories = ["Lust und Laune", "Nudeln", "Fleisch","Reis, Bulgur, Couscous","Suppe","Suess"]



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
       

class MainHandler(Handler):
    def get(self):
        self.render("index.html")

app = webapp2.WSGIApplication([('/', MainHandler),
                            ('/add_meal', MealAdd)],
                              debug=True)
