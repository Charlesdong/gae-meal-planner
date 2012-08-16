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
import random
import hashlib
import re

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
            table.append(result.get())
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

# Classes for loging in and singing up Users

class Login(Handler):
    
    def get(self, error=""):
        self.render("login.html", error = error)

    def post(self, email="", pwd=""):
        
        pwd = self.request.get("pwd")
        pwd = hashlib.sha256(pwd)
        pwd = str(pwd.hexdigest())
        
        user = model.User.all().filter("email =", self.request.get("email"))
        
        if user.get() and user.get().pwd == pwd:
            self.redirect("/show")
        else:
            error = "Login ungültig. Bitte versuchen Sie es nochmal!"
            self.render("login.html", error = error)

class SignUp(Handler):

    def get(self, error=""):
        self.render("signup.html", error=error)

    def post(self, name="", lastname="", email="", pwd="", pwd_check=""):
        name = self.request.get("name")
        lastname = self.request.get("lastname")
        email = self.request.get("email")
        pwd = self.request.get("pwd") 
        pwd_check = self.request.get("pwd_check")

        # validate the form
        
        user = model.User.all().filter("email =", self.request.get("email"))
           
        if name and lastname and email and pwd and pwd_check:
            if user.get():
                error = "Emailadresse ist bereits registriert. Bitte wählen Sie eine andere!"
                self.render("signup.html", error = error)
            else:    
                if pwd == pwd_check:
                    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
                        pwd = hashlib.sha256(pwd)
                        pwd = str(pwd.hexdigest())
                        u = model.User(name = name, lastname = lastname, email = email, pwd = pwd)
                        u.put()
                        self.redirect("/")
                    else:
                        error = "Emailadresse fehlerhaft!"
                        self.render("signup.html", error = error)
                else:
                    error = "Die Paßwörter stimmen nicht miteinander überein!"
                    self.render("signup.html", error = error)
        else:
            error = "Bitte alle Felder ausfüllen!"
            self.render("signup.html", error = error)
            
        



# Meal Handler Classes

class MealAdd(Handler):
    
    def render_addmeal(self,content="", error="", day_date=""):
        self.render("add_meal.html", content = model.meal_categories, error = error, day_date = day_date)

    def get(self, date=""):
        self.render("add_meal.html",content = model.meal_categories, day_date=date)

    def post(self, day_date=""):
        key_name=""
        for i in range(1,10):
           key_name = key_name + random.choice(["a","b","c","d","e","f","g","h","i","j","k","l","n","m","o","p","q","r","s","t","u","v","w","x","y","z"]) 
        key_name = key_name+str(random.randint(1000,9999))

        name = self.request.get("name")
        category = self.request.get("selection")
        ingredients = self.request.get("ingredients")
        reference = self.request.get("reference")
        day_date = self.request.get("day_date")

        if name:
            m = model.Meal(key_name = key_name, name = name, category = category, ingredients = ingredients, reference = reference)
            m.put()
            # go to where you came from

            self.redirect("/show_meal_list/"+day_date)
        else:
            error = "Bitte Namen angeben!"
            content = model.meal_categories
            self.render_addmeal(content, error, day_date)
       
class MealDel(Handler):
    
    def render_meal(self, key_name="", day_date=""):
        meal = model.Meal.get_by_key_name(key_name)

        if meal:
            self.render("del_meal.html", meal = meal, day_date=day_date)
        else:
            error = "Dieses Gericht ist nicht (mehr) existent!"
            self.render("del_meal.html", meal = None, error=error, day_date = day_date) 
    
    def get(self, key_name, day_date=""):
        self.render_meal(key_name = key_name, day_date=day_date)       
    
    def post(self, key_name="", day_date=""):
        m = model.Meal.get_by_key_name(key_name)
        
        days_to_cleanup = model.db.GqlQuery("SELECT * FROM Day WHERE meal_key_name = :meal_key_name", meal_key_name = m.key().name())

        for day in days_to_cleanup:
            day.meal_name = ""
            day.meal_key_name = ""
            day.put()
        
        m.delete()
        # go to where you came from
        day_date = self.request.get("day_date")
        self.redirect("/show_meal_list/"+day_date)

class MealShowList(Handler):

    def get(self, day_object_date=actual_day, sort_criteria = "", meal_categories = []):
        if sort_criteria:
            meal_list = model.db.GqlQuery("SELECT * FROM Meal WHERE category = :sort_criteria ORDER BY category DESC", sort_criteria) 
            self.render("show_meal_list.html", meal_list = meal_list, day_date = day_date, meal_categories = model.meal_categories, sort_criteria = sort_criteria)
        else:
            meal_list = model.Meal.all()
            self.render("show_meal_list.html", meal_list = meal_list, day_date = day_object_date, meal_categories = model.meal_categories) 


    def post(self, day_date="", sort_criteria=""):
        
        day_date = self.request.get("day_date")
        sort_criteria = self.request.get("sort_criteria")
        
        if sort_criteria == "all":
            meal_list = model.db.GqlQuery("SELECT * FROM Meal")
        else:
            meal_list = model.db.GqlQuery("SELECT * FROM Meal WHERE category = :sort_criteria ORDER BY category DESC", sort_criteria = self.request.get("sort_criteria"))
        
        self.render("show_meal_list.html", meal_list = meal_list, day_date = day_date, meal_categories = model.meal_categories, sort_criteria = sort_criteria)


class MealShowDetail(Handler):

    def get(self, day_object_date, meal_key_name):
        
        #Constructing the Back Link

        day_object_date = day_object_date.replace('-',' ').split()
        day_object_date = datetime.date(int(day_object_date[0]),int(day_object_date[1]),int(day_object_date[2])) 
        day_object_date = day_object_date.isocalendar()
        backlink = "/show/"+str(day_object_date[0])+"/"+str(day_object_date[1])

        # Getting the right Meal
        meal = model.Meal.get_by_key_name(meal_key_name)
        
        # Jump to the template
        self.render("show_meal_detail.html", meal = meal, backlink = backlink)




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
        tab = construct_table(year, cw)
        for day in tab:
            m = model.Meal.all().filter('day =', day.key())
            if m.get():
               day.meal_name = m.get().name
               day.meal_key_name = m.get().key().name()
               day.put()

        self.render("show_planner.html", days = tab, nav = nav)

class EntryCommit(Handler):
    
    def get(self, day_object_date, meal_key_name):

        day_object_date = day_object_date.replace('-',' ').split()
        day_object_date = datetime.date(int(day_object_date[0]),int(day_object_date[1]),int(day_object_date[2])) 
        
        d = model.Day.all().filter('date =', day_object_date)
        m = model.Meal.get_by_key_name(meal_key_name)
        
        meal = model.Meal(key_name=m.key().name(),name=m.name, category=m.category, ingredients = m.ingredients, reference = m.reference)
        # copy values from queried Object to new Object
        meal.day = m.day
        # Value not already in ListProperty then append it
        if d.get().key() not in m.day:
            meal.day.append(d.get().key())
        meal.put()
        # hier Parameter für korrekten Rücksprung errechnen (Jahr//KW)

        day_object_date = day_object_date.isocalendar()

        self.redirect("/show/"+str(day_object_date[0])+"/"+str(day_object_date[1]))

class EntryRemove(Handler):

    def get(self, day_object_date, meal_key_name):
        
        day_object_date = day_object_date.replace('-',' ').split()
        day_object_date = datetime.date(int(day_object_date[0]),int(day_object_date[1]),int(day_object_date[2])) 
        
        d = model.Day.all().filter('date =', day_object_date)
        m = model.Meal.get_by_key_name(meal_key_name)
        meal = model.Meal(key_name=m.key().name(),name=m.name, category=m.category, ingredients = m.ingredients, reference = m.reference)
        day = model.Day(name = d.get().name, date = d.get().date, meal_name = None, meal_key_name = None) 
        meal.day = m.day
        meal.day.remove(d.get().key())
        d.get().delete()
        meal.put()
        day.put()
        # hier Parameter für korrekten Rücksprung errechnen (Jahr//KW)

        day_object_date = day_object_date.isocalendar()

        self.redirect("/show/"+str(day_object_date[0])+"/"+str(day_object_date[1]))


class MainHandler(Handler):
    def get(self):
        self.redirect("/login")

app = webapp2.WSGIApplication([('/', MainHandler),
                            ('/add_meal', MealAdd),
                            ('/login', Login),
                            ('/signup', SignUp),
                            ('/add_meal/(2\d{3}-\d{2}-\d{2})', MealAdd),
                            ('/del_meal/(\w+\d{4})/(2\d{3}-\d{2}-\d{2})', MealDel),
                            ('/show_meal_list', MealShowList),
                            ('/show_meal_list/(2\d{3}-\d{2}-\d{2})/(\w+)/(\w+)', MealShowList),
                            ('/show_meal_list/(2\d{3}-\d{2}-\d{2})/(\w+)', MealShowList),
                            ('/show_meal_list/(2\d{3}-\d{2}-\d{2})', MealShowList),
                            ('/show_meal_detail/(2\d{3}-\d{2}-\d{2})/(\w+\d{4})', MealShowDetail),
                            ('/show', ShowPlanner),
                            ('/show/(2\d{3})/([1-5]{1}[0-9]{1}|[1-9])', ShowPlanner),
                            ('/commit_entry/(2\d{3}-\d{2}-\d{2})/(\w+\d{4})', EntryCommit),
                            ('/remove_entry/(2\d{3}-\d{2}-\d{2})/(\w+\d{4})', EntryRemove)],
                              debug=True)
