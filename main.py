#!/usr/bin/env python
#-*- coding: utf-8 -*-

''' 
Meal-Planner 

Tracks your plans for what to eat on a weekly base. 

V.0.1 by Marcus Kemper

kemper.mt@googlemail.com 
'''


 
# ... ("template.html", variable_im_template = variable aus function)


import webapp2
import jinja2
import os
import datetime
import time


import model



template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

# Helper functions and things like that...

day_names = {0:"Montag",1:"Dienstag",2:"Mittwoch",3:"Donnerstag",4:"Freitag",5:"Samstag",6:"Sonntag"}

actual_day = datetime.date.today()

actual_calendar_week = int(time.strftime("%W",time.struct_time(time.localtime())))

actual_year = int(time.strftime("%Y",time.struct_time(time.localtime())))


def get_week(year, cw):
    first_monday = 4 - datetime.date(year,1,4).weekday()
    monday_of_kw = first_monday + (cw - 1)*7
    list = range(monday_of_kw, monday_of_kw + 7)
    return list

def get_date(year, day_of_year):
    d = datetime.datetime(year,1,1)+datetime.timedelta(day_of_year - 1)
    name = day_names[d.weekday()]
    date = (name, d.day, d.month, d.year)
    return date

def construct_table(year, cw):
    w = get_week(year, cw)
    table = []    
    for data in w:
        data = get_date(year, data)
        data_date = datetime.date(data[3],data[2],data[1])
        result = model.Day.all().filter('date =', data_date)
        if not result.get():
            d = model.Day(name = str(data[0]), date = data_date)
            d.put()
            table.append(d)
        else:
            print "Eintrag schon vorhanden!"
            table.append(result)
    return table    

# Handler class for the template engine

class Handler(webapp2.RequestHandler):
  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)

  def render_str(self, template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

  def render(self, template, **kw):
    self.write(self.render_str(template, **kw))

# Meal Handler Classes

class MealAdd(Handler):
    
    def render_addmeal(self,content="", error=""):
        self.render("add_meal.html", content = model.meal_categories, error = error)

    def get(self):
        self.render("add_meal.html",content = model.meal_categories)

    def post(self):
        name = self.request.get("name")
        category = self.request.get("selection")
        ingredients = self.request.get("ingredients")
        reference = self.request.get("reference")
        
        if name:
            m = model.Meal(name = name, category = category, ingredients = ingredients, reference = reference)
            m.put()
            self.redirect("/show_meal_list")
        else:
            error = "Bitte Namen angeben!"
            content = model.meal_categories
            self.render_addmeal(content, error)
       
class MealDel(Handler):
    
    def render_meal(self, _id=""):
        _id = int(_id)
        meal = model.Meal.get_by_id(_id)

        if meal:
            self.render("del_meal.html", meal = meal)
        else:
            error = "Dieses Gericht ist nicht (mehr) existent!"
            self.render("del_meal.html", meal = None, error=error) 
    
    def get(self, _id):
        self.render_meal(_id = _id)       
    
    def post(self, _id=""):
        _id = int(_id)
        m = model.Meal.get_by_id(_id)
        m.delete()
        self.redirect("/show_meal_list")

class MealShowList(Handler):

    def get(self, day_object=model.Day):
        meal_list = model.db.GqlQuery("SELECT * FROM Meal ORDER BY category DESC")
        self.render("show_meal_list.html", meal_list = meal_list, day = day_object)

# Day Handler Classes

class ShowPlanner(Handler):

    def get(self, year=actual_year, cw=actual_calendar_week):
        year = int(year)
        cw = int(cw)
        # setting up navigation
        if cw == 1:
            back_cw = 52  
            back_year = (year - 1)
        else:
            back_cw = cw - 1
            
            back_year = year
        if cw == 52:
            forward_cw = 1 
            forward_year = (year + 1)
        else:
            forward_cw = cw + 1
            forward_year = year

        nav = (year, cw, back_year, back_cw, forward_year, forward_cw)
        t = construct_table(year, cw)
        self.render("show_planner.html", days = t, nav = nav)

class EntryCommit(Handler):
    
    def get(self, day_object_date, meal_id):
        self.redirect("/")


class MainHandler(Handler):
    def get(self):
        self.redirect("/show")

app = webapp2.WSGIApplication([('/', MainHandler),
                            ('/add_meal', MealAdd),
                            ('/del_meal/(\d+)', MealDel),
                            ('/show_meal_list', MealShowList),
                            ('/show_meal_list/(2\d{3}-\d{2}-\d{2})', MealShowList),
                            ('/show', ShowPlanner),
                            ('/show/(2\d{3})/([1-5]{1}[0-9]{1}|[1-9])', ShowPlanner),
                            ('/commit_entry/(2\d{3}-\d{2}-\d{2})/(\d+)', EntryCommit)],
                              debug=True)
