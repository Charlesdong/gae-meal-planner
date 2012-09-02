#!/usr/bin/env python
#-*- coding: utf-8 -*-

''' 
Meal-Planner 

Tracks your plans for what to eat on a weekly base. 

V.0.2 by Marcus Kemper

kemper.mt@googlemail.com 
'''


 
# ... ("template.html", variable_im_template = variable aus function)


import webapp2
import jinja2
import os
import datetime
import random
import hashlib
import re
import json

import model
import helper

# delivers date and time formats
datehelper = helper.DateHelper()

# collects all active shoppinglists
shoppinglist_dict = {}

# unique session id
SESSION_ID = ""

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

# Constructs the calendar week table and populates it with model.Day objects
def construct_table(user, year, cw):
    w = datehelper.get_week(year, cw)
    table = []    
    for data in w:
        day_date = datehelper.get_date(year, data)
                
        #get current logged-in user from database
        au = model.Authenticated.get_by_key_name(user)
        
        # look for timetable of current logged-in user
        result = model.db.GqlQuery("SELECT * FROM Day WHERE date = :daydate AND owner = :owner", daydate = day_date, owner = au.user)
        
        # if it's not there create it
        if not result.get():
            d = model.Day(name = datehelper.get_day_name(str(day_date)), date = day_date, owner = au.user )
            d.put()
            table.append(d)
        else:
            table.append(result.get())
    return table  

# generates sha256 hashstring
def hash_str(string):
    hashed_string = hashlib.sha256(string)
    hashed_string = str(hashed_string.hexdigest())
    return hashed_string

# generates a unique Session ID
def generate_SESSION_ID():
    global SESSION_ID
    for i in range(1,10):
        SESSION_ID = SESSION_ID + random.choice(["a","b","c","d","e","f","g","h","i","j","k","l","n","m","o","p","q","r","s","t","u","v","w","x","y","z"]) 
    SESSION_ID = SESSION_ID+str(random.randint(1000,9999))
    SESSION_ID = hash_str(SESSION_ID)
    return SESSION_ID

# Handler class for the template engine

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

# verify whether user is logged in or not and if, since when
    
    def verify_user(self, user):
        au = model.Authenticated.get_by_key_name(user)
        if not au:
            self.redirect("/login")
        else:
            diff = datetime.datetime.now() - au.logged_in_at 
            if diff.seconds > 1800:
                print diff
                au.delete()
                error = u"Ihre Benutzersitzung ist abgelaufen. Sie werden zum Login weitergeleitet..."
                self.render("error.html", error = error)
               
            else:
                return au.user              
           
class Error(Handler):  
    
    def get(self, error=""):
        self.render("error.html", error = error)

# cron class for cleaning up the authenticated db            
class CleanUp(Handler):
    
    def get(self):
        users = model.Authenticated.all()
        for user in users:
            diff = datetime.datetime.now() - user.logged_in_at
            if diff.days >= 1:
                user.delete()
                
          
# Classes for loging in and singing up Users
class Login(Handler):
    
    def get(self, error="", thanks=""):
        self.render("login.html", error = error, thanks = thanks)

    def post(self, email="", pwd=""):
        
        pwd = self.request.get("pwd")
        pwd = hash_str(pwd)
        
        user = model.User.all().filter("email =", self.request.get("email"))
        
        # login success
        if user.get() and user.get().pwd == pwd:
                       
            # retrieve login and generate SESSION_ID
            global SESSION_ID
            SESSION_ID = generate_SESSION_ID()
            user = user.get().email
            
            # generate shopping-list for user
            global shoppinglist_dict
            
            shoppinglist = helper.ShoppingList(user)
            
            #adding to dictionary
            shoppinglist_dict.update({SESSION_ID:shoppinglist})
            
            # write login and SESSION_ID to db
            a = model.Authenticated(user = user, key_name = SESSION_ID)
            a.put()
            self.redirect("/show/"+SESSION_ID)
                    
        # login failed
        else:
            error = u"Login ungültig. Bitte versuchen Sie es nochmal!"
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
            

class Logout(Handler):       
    
    def get(self, user):
        user = model.Authenticated.get_by_key_name(user)
        if user:
            user.delete()
            self.redirect("/login")
        else:
            self.redirect("/login")
            
        



# Meal Handler Classes

class MealAdd(Handler):
    
    def render_addmeal(self, user, content="", error="", day_date=""):
        
        # is there valid logged in user?
        self.verify_user(user)
            
        self.render("add_meal.html", user = user, content = model.meal_categories, error = error, day_date = day_date)

    def parse_ingredients(self, ingredients):
        
        # remove whitespaces
        ingredients = ingredients.replace(' ','')
        # transform strings into a list of strings
        ingredients = ingredients.split(',')
        
        return ingredients
        
    
    
    def get(self, user, date=""):
        
        # is there valid logged in user?
        self.verify_user(user)
                      
        self.render("add_meal.html", user = user, content = model.meal_categories, day_date=date)

    def post(self, user, day_date=""):
        
        # is there valid logged in user?
        au = self.verify_user(user)
            
        key_name=""
        for i in range(1,10):
            key_name = key_name + random.choice(["a","b","c","d","e","f","g","h","i","j","k","l","n","m","o","p","q","r","s","t","u","v","w","x","y","z"]) 
        key_name = key_name+str(random.randint(1000,9999))

        name = self.request.get("name")
        category = self.request.get("selection")
        ingredients = self.parse_ingredients(self.request.get("ingredients"))
        reference = self.request.get("reference")
        day_date = self.request.get("day_date")
      
        if name:
            m = model.Meal(key_name = key_name, name = name, category = category, ingredients = ingredients, reference = reference, owner = au)
            m.put()
            # go to where you came from
            self.redirect("/show_meal_list/"+user+"/"+day_date)
        else:
            error = "Bitte Namen angeben!"
            content = model.meal_categories
            self.render_addmeal(user, content, error, day_date)
   
class MealDel(Handler):
    
    def render_meal(self, user, key_name="", day_date=""):
        
        # is there valid logged in user?
        self.verify_user(user)
                
        meal = model.Meal.get_by_key_name(key_name)

        if meal:
            self.render("del_meal.html", user = user, meal = meal, day_date=day_date)
        else:
            error = "Dieses Gericht ist nicht (mehr) existent!"
            self.render("del_meal.html", user = user, meal = None, error=error, day_date = day_date) 

    def get(self, user, key_name, day_date=""):
        
        # is there valid logged in user?
        self.verify_user(user)
        
        self.render_meal(user = user, key_name = key_name, day_date=day_date)       
    
    def post(self, user, key_name="", day_date=""):
        
        # is there valid logged in user?
        au = self.verify_user(user)
        
        m = model.Meal.get_by_key_name(key_name)
        
        days_to_cleanup = model.db.GqlQuery("SELECT * FROM Day WHERE meal_key_name = :meal_key_name AND owner = :owner", meal_key_name = m.key().name(), owner = au)

        for day in days_to_cleanup:
            day.meal_name = ""
            day.meal_key_name = ""
            day.put()
        
        m.delete()
        # go to where you came from
        day_date = self.request.get("day_date")
        self.redirect("/show_meal_list/"+user+"/"+day_date)

class MealShowList(Handler):

    def get(self, user, day_date=datehelper.get_actual_day, sort_criteria = "", meal_categories = []):
        
        # is there valid logged in user?
        au = self.verify_user(user)
        
        # if there is a sorting selection, just show sorted meals
        if sort_criteria:
            meal_list = model.db.GqlQuery("SELECT * FROM Meal WHERE category = :sort_criteria ORDER BY category DESC AND owner = :owner", sort_criteria, owner = au) 
            self.render("show_meal_list.html", user = user, meal_list = meal_list, day_date = day_date, meal_categories = model.meal_categories, sort_criteria = sort_criteria)
        # otherwise show the whole list belonging to the user
        else:
            meal_list = model.db.GqlQuery("SELECT * FROM Meal WHERE owner = :owner", owner = au)
            self.render("show_meal_list.html", user = user, meal_list = meal_list, day_date = day_date, meal_categories = model.meal_categories) 


    def post(self, user, day_date="", sort_criteria=""):
        
        # is there valid logged in user?
        au = self.verify_user(user)
        
        day_date = self.request.get("day_date")
        sort_criteria = self.request.get("sort_criteria")
        
        if sort_criteria == "all":
            meal_list = model.db.GqlQuery("SELECT * FROM Meal WHERE owner = :owner", owner = au)
        else:
            meal_list = model.db.GqlQuery("SELECT * FROM Meal WHERE category = :sort_criteria ORDER BY category DESC WHERE owner = :owner", owner = au, sort_criteria = self.request.get("sort_criteria"))
        
        self.render("show_meal_list.html", user = user, meal_list = meal_list, day_date = day_date, meal_categories = model.meal_categories, sort_criteria = sort_criteria)


class MealShowDetail(Handler):

    def get(self, user, day_date, meal_key_name):
        
        # is there valid logged in user?
        self.verify_user(user)
        
        #Constructing the Back Link

        year_cw = datehelper.get_year_cw(day_date)
        backlink = "/show/"+user+"/"+str(year_cw[0])+"/"+str(year_cw[1])

        # Getting the right Meal
        meal = model.Meal.get_by_key_name(meal_key_name)
        
        # Jump to the template
        self.render("show_meal_detail.html", user = user, day_date = day_date, meal = meal, backlink = backlink)

   
# Day Handler Classes

class ShowPlanner(Handler):

    def get(self, user, year=datehelper.actual_year, cw=datehelper.actual_calendar_week):
        
        # is there valid logged in user?
        self.verify_user(user)
        
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

        nav = (year, cw, back_year, back_cw, forward_year, forward_cw, user)
        tab = construct_table(user, year, cw)
        for day in tab:
            #m = model.Meal.all().filter('day =', day.key())
            
            m = model.db.GqlQuery("SELECT * FROM Meal WHERE day = :daykey", daykey = day.key())
            if m.get():
                day.meal_name = m.get().name
                day.meal_key_name = m.get().key().name()
                day.put()
        
        self.render("show_planner.html", user = user, days = tab, nav = nav)

class EntryCommit(Handler):
    
    def get(self, user, day_date, meal_key_name):
        
        # is there valid logged in user?
        au = self.verify_user(user)
        
        day_date = datehelper.gen_date_obj(day_date)
        
        d = model.db.GqlQuery("SELECT * FROM Day WHERE date = :daydate AND owner = :owner", daydate = day_date, owner = au)      
        #d = model.Day.all().filter('date =', day_date)
        m = model.Meal.get_by_key_name(meal_key_name)
        
        meal = model.Meal(key_name=m.key().name(),name=m.name, category=m.category, ingredients = m.ingredients, reference = m.reference, owner = au)
        
        # copy values from queried Object to new Object
        meal.day = m.day
        
        # Value not already in ListProperty then append it
        if d.get().key() not in m.day:
            meal.day.append(d.get().key())
        meal.put()
        
        # hier Parameter für korrekten Rücksprung errechnen (Jahr//KW)
        year_cw = datehelper.get_year_cw(str(day_date))

        self.redirect("/show/"+user+"/"+str(year_cw[0])+"/"+str(year_cw[1]))

class EntryRemove(Handler):

    def get(self, user, day_date, meal_key_name):
        
        # is there valid logged in user?
        au = self.verify_user(user)
        
        # generates datetime object
        day_date = datehelper.gen_date_obj(day_date)
        
        # lookup db for correct day and meal
        d = model.db.GqlQuery("SELECT * FROM Day WHERE date = :daydate AND owner = :owner", daydate = day_date, owner = au)
        #d = model.Day.all().filter('date =', day_date)
        m = model.Meal.get_by_key_name(meal_key_name)
        
        meal = model.Meal(key_name=m.key().name(),name=m.name, category=m.category, ingredients = m.ingredients, reference = m.reference)
        # erases meal from day object
        day = model.Day(name = d.get().name, date = d.get().date, meal_name = None, meal_key_name = None, owner = d.get().owner) 
        meal.day = m.day
        meal.day.remove(d.get().key())
        d.get().delete()
        meal.put()
        day.put()
        
        # hier Parameter für korrekten Rücksprung errechnen (Jahr//KW)
        year_cw = datehelper.get_year_cw(str(day_date))

        self.redirect("/show/"+user+"/"+str(year_cw[0])+"/"+str(year_cw[1]))

# Displays the actual Shopping-List
class ShoppingListShow(Handler):
    
    def get(self, user, year, cw):
        
        # is there valid logged in user?
        self.verify_user(user)
        
        #get current logged-in user from database
        
        #au = model.Authenticated.get_by_key_name(user)
        
        #if not au:
        #   self.redirect("/")
            
        # get shoppinglist from database
       
        #sl = model.ShoppingList.all().filter("owner =", au.user)
        
        #global shoppinglist_dict
        sl = shoppinglist_dict.get(user)
        
        if not sl or not sl.items:
            backlink = "/show/"+user+"/"+str(year)+"/"+str(cw)
            self.render("shoppinglist.html", user = user, backlink = backlink)
        else:
                      
            # generate json object
            sl = json.dumps(sl.items)
          
            # assembling the backlink url
            year = year
            cw = cw
            backlink = "/show/"+user+"/"+str(year)+"/"+str(cw)
            
            self.render("shoppinglist.html", user = user, backlink = backlink, sl = sl)

class ShoppingListAdd(Handler):
    
    def post(self, user, day_date):
        
        # is there valid logged in user?
        self.verify_user(user)
        
        # converting json list to python list
                 
        data = json.loads(self.request.POST['data'])
        
        # adding items to shopping-list
        #global shoppinglist_dict
        sl = shoppinglist_dict.get(user)
        
        # updating data in object with data from json transmission
        sl.update_list(data)
        
        # save all to database
        sl.make_persistent(user)
        
        # Constructing the Back Link

        year_cw = datehelper.get_year_cw(day_date)
        backlink = "/show/"+user+"/"+str(year_cw[0])+"/"+str(year_cw[1])

        # Jump to Meal-Planner 
        self.redirect(backlink)

class ShoppingListDel(Handler):
    
    def post(self, user):
        
        # is there valid logged in user?
        self.verify_user(user)
        
        # converting json string to python string
                 
        data = json.loads(self.request.POST['data'])
        
        # adding items to shopping-list
        #global shoppinglist_dict
        sl = shoppinglist_dict.get(user)
        
        # updating data in object with data from json transmission
        sl.remove_item(user,data)
        
        # save all to database
        sl.make_persistent(user)
        
        


class Debug(Handler):
    
    def get(self):
        
        global shoppinglist_dict
        for key in shoppinglist_dict:
            self.write(shoppinglist_dict.items())
        

class MainHandler(Handler):
    def get(self):
        self.redirect("/login")
        
app = webapp2.WSGIApplication([('/', MainHandler),
                            ('/debug', Debug),
                            ('/add_meal', MealAdd),
                            ('/login', Login),
                            ('/logout/([a-fA-F\d]{64})', Logout),
                            ('/error', Error),
                            ('/signup/iwenttherebytrain', SignUp),
                            ('/tasks/cleanup', CleanUp),
                            ('/shoppinglist/([a-fA-F\d]{64})/(2\d{3})/([1-5]{1}[0-9]{1}|[1-9])', ShoppingListShow),
                            ('/shoppinglist/add/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})', ShoppingListAdd),
                            ('/shoppinglist/del/([a-fA-F\d]{64})', ShoppingListDel),
                            ('/add_meal/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})', MealAdd),
                            ('/del_meal/([a-fA-F\d]{64})/(\w+\d{4})/(2\d{3}-\d{2}-\d{2})', MealDel),
                            ('/show_meal_list/([a-fA-F\d]{64})', MealShowList),
                            ('/show_meal_list/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})/(\w+)/(\w+)', MealShowList),
                            ('/show_meal_list/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})/(\w+)', MealShowList),
                            ('/show_meal_list/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})', MealShowList),
                            ('/show_meal_detail/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})/(\w+\d{4})', MealShowDetail),
                            ('/show/([a-fA-F\d]{64})', ShowPlanner),
                            ('/show', ShowPlanner),
                            ('/show/([a-fA-F\d]{64})/(2\d{3})/([1-5]{1}[0-9]{1}|[1-9])', ShowPlanner),
                            ('/commit_entry/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})/(\w+\d{4})', EntryCommit),
                            ('/remove_entry/([a-fA-F\d]{64})/(2\d{3}-\d{2}-\d{2})/(\w+\d{4})', EntryRemove)],
                              debug=True)
