#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "zg2319"
DB_PASSWORD = "c4BeA0orDZ"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above

engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT reid FROM reservation_reserved")
  reservation = []
  for result in cursor:
    reservation.append(result[0])  # can also be accessed using result[0]
  cursor.close()




  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = reservation)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#

@app.route('/search_reservation', methods=['POST'])
def search():
  reid = request.form['name']
  #print(reid)
  cmd = 'SELECT reserve_time, no_guests, rid, uid FROM reservation_reserved WHERE reid = (:reid1)';
  cursor = g.conn.execute(text(cmd), reid1 = reid)
  res = cursor.fetchone()

  if not res:
    return render_template("no_result.html", data = reid)

  reserve_time, no_guests, rid, uid = res
  cursor.close()

  cmd = 'SELECT user_name FROM users WHERE uid = (:uid1)';
  cursor = g.conn.execute(text(cmd), uid1 = uid)
  user_name = cursor.fetchone()[0]
  cursor.close()

  context = dict(user_name = user_name, reserve_time=reserve_time, no_guests=no_guests, rid=rid, uid=uid, reid = reid)
  return render_template("search_reservation.html", **context)


@app.route('/search_order', methods=['POST'])
def search_order():
  oid = request.form['name']
  cmd = 'SELECT O.o_phone, O.o_add, O.o_name, O.tip, O.payment, R.res_name, P.uid, DG.dg_name, DG.dg_phone FROM restaurants R, place P, order_assigned_to O, delivery_guy DG WHERE R.rid=P.rid AND O.oid=P.oid  AND O.gid=DG.gid AND O.oid = (:oid1)';
  cursor = g.conn.execute(text(cmd), oid1 = oid)
  res = cursor.fetchone()

  if not res:
    return render_template("no_result.html", data = oid)

  o_phone, o_add, o_name, tip, payment, res_name, uid, dg_name, dg_phone = res
  cursor.close()

  cmd = 'SELECT SUM(D.price) FROM order_assigned_to O, include I, dish_provide D WHERE  O.oid=I.oid AND I.did=D.did AND I.rid=D.rid AND O.oid=(:oid1);';
  cursor = g.conn.execute(text(cmd), oid1 = oid)
  total = float(cursor.fetchone()[0]) + float(tip)
  cursor.close()

  cmd = 'SELECT user_name FROM users WHERE uid = (:uid1)';
  cursor = g.conn.execute(text(cmd), uid1 = uid)
  user_name = cursor.fetchone()[0]
  cursor.close()

  context = dict(user_name = user_name, o_phone=o_phone, o_add=o_add, o_name=o_name, tip=tip, payment=payment, oid = oid, res_name = res_name, uid = uid, 
    dg_name = dg_name, dg_phone = dg_phone, total = total)

  return render_template("search_order.html", **context)


@app.route('/submit_reservation', methods=['POST'])
def submit_reservation():
  cursor = g.conn.execute("SELECT rid, res_name FROM restaurants")
  names = []
  for result in cursor:
    names.append([result['res_name'], result['rid']])
  cursor.close()

  cursor = g.conn.execute("SELECT MAX(uid) FROM users")
  max_uid = cursor.fetchone()[0]
  cursor.close()

  context = dict(data = names, max_uid = max_uid)

  return render_template("submit_reservation.html", **context)


@app.route('/reservation_summary', methods = ['POST', 'GET'])
def get_res_name():
  rid = request.form['rid']
  # reserve_time = datetime.strptime(request.form['time'], "%Y-%m-%d").date()
  reserve_time = str(request.form['time'])
  no_guests = request.form['num_guests']
  uid = request.form['userid']

  cursor = g.conn.execute("SELECT MAX(reid) FROM reservation_reserved")
  reid = int(cursor.fetchone()[0]) + 1
  cursor.close()
  cursor = g.conn.execute("SELECT res_name FROM restaurants WHERE rid = %s", (rid,))
  res_name = cursor.fetchone()[0]
  cursor.close()

  cmd = 'SELECT user_name FROM users WHERE uid = (:uid1)';
  cursor = g.conn.execute(text(cmd), uid1 = uid)
  user_name = cursor.fetchone()[0]
  cursor.close()

  try:
    g.conn.execute('INSERT INTO reservation_reserved(reserve_time, no_guests, reid, rid, uid) VALUES (%s, %s, %s, %s, %s)', (reserve_time, no_guests, reid, rid, uid));

  except:
    return render_template("wrong_input.html")

  return render_template("reservation_summary.html", user_name = user_name, reserve_time = reserve_time, no_guests = no_guests, reid = reid, res_name = res_name, uid = uid)



@app.route('/submit_order', methods=['POST'])
def submit_order():
  
  cmd = 'SELECT rid, res_name FROM restaurants';
  cursor = g.conn.execute(text(cmd))
  restaurants = []
  for result in cursor:
    restaurants.append([result[0], result[1]])
  cursor.close()
  return render_template("submit_order.html", restaurants=restaurants)


@app.route('/choose_dishes', methods=['POST', 'GET'])
def choose_dishes():
  rid =  request.form['rid']
  cmd = 'SELECT dish_name, price FROM restaurants res JOIN dish_provide dp ON res.rid = dp.rid WHERE res.rid=(:rid1)';
  cursor = g.conn.execute(text(cmd), rid1 = rid)
  dishes_price = []
  for result in cursor:
    dishes_price.append([result['dish_name'], result['price']])
  cursor.close()

  cmd = 'SELECT res_name FROM restaurants WHERE rid=(:rid1)';
  cursor = g.conn.execute(text(cmd), rid1 = rid)
  res_name = cursor.fetchone()[0]
  cursor.close()

  cursor = g.conn.execute("SELECT MAX(uid) FROM users")
  max_uid = cursor.fetchone()[0]
  cursor.close()

  return render_template("choose_dishes.html", dishes_price=dishes_price, rid = rid, res_name = res_name, max_uid = max_uid)

@app.route('/order_summary', methods=['POST', 'GET'])
def order_summary():
  rid = request.form['rid']
  o_name = request.form['o_name']
  o_add = request.form['o_add']
  o_phone = request.form['o_phone']
  tip = int(request.form['tip'])
  payment = request.form['payment']
  uid = request.form['uid']

  cmd = 'SELECT user_name FROM users WHERE uid = (:uid1)';
  cursor = g.conn.execute(text(cmd), uid1 = uid)
  user_name = cursor.fetchone()[0]
  cursor.close()

# Get the name of restaurant
  cmd = 'SELECT res_name FROM restaurants WHERE rid=(:rid1)';
  cursor = g.conn.execute(text(cmd), rid1 = rid)
  res_name = cursor.fetchone()[0]
  cursor.close()

# Generate oid
  cmd = 'SELECT MAX(oid) FROM order_assigned_to'
  cursor = g.conn.execute(text(cmd))
  oid = int(cursor.fetchone()[0]) + 1
  cursor.close()

# Generate gid and get information of delivery_guy
  gid = oid % 10 + 1
  cmd = 'SELECT dg_name, dg_phone FROM delivery_guy WHERE gid=(:gid1)';
  cursor = g.conn.execute(text(cmd), gid1 = gid)
  res = cursor.fetchone()
  dg_name, dg_phone = res[0], res[1]
  cursor.close()

# Deal with dishes and calculate the total price
  cmd = 'SELECT dish_name, price, did FROM restaurants res JOIN dish_provide dp ON res.rid = dp.rid WHERE res.rid=(:rid1)';
  cursor = g.conn.execute(text(cmd), rid1 = rid)
  dishes_price = []
  for result in cursor:
    dishes_price.append([result['dish_name'], result['price'], result['did']])

  total = tip
  quant = 0

  for i in dishes_price:
  	quant += int(request.form[i[0]])
  if quant == 0:
  	return render_template("no_dishes.html")

  # Insert into order_assigned_to and place
  g.conn.execute('INSERT INTO order_assigned_to(oid, gid, o_name, o_add, o_phone, tip, payment) VALUES (%s, %s, %s, %s, %s, %s, %s)', (oid, gid, o_name, o_add, o_phone, tip, payment))
  g.conn.execute('INSERT INTO place(rid, uid, oid) VALUES (%s, %s, %s)', (rid, uid, oid))

  for i in dishes_price:
    quant = int(request.form[i[0]])
    if quant!=0:
      did = i[2]
      price = float(i[1])
      total += price * quant
      for i in range(quant):
        cmd = 'SELECT MAX(iid) FROM include'
        cursor = g.conn.execute(text(cmd))
        iid = int(cursor.fetchone()[0]) + 1
        cursor.close()
        g.conn.execute('INSERT INTO include(oid, did, rid, iid) VALUES (%s, %s, %s, %s)', (oid, did, rid, iid))

  return render_template("order_summary.html", user_name = user_name, o_phone=o_phone, o_add=o_add, o_name=o_name, tip=tip, payment=payment, oid = oid, res_name = res_name, uid = uid, 
    dg_name = dg_name, dg_phone = dg_phone, total = total)


@app.route('/user_create', methods=['POST', 'GET'])
def user_create():
  user_name = request.form["name"]
  cmd = 'SELECT MAX(uid) FROM users'
  cursor = g.conn.execute(text(cmd))
  uid = int(cursor.fetchone()[0]) + 1
  cursor.close()

  g.conn.execute('INSERT INTO users(user_name, uid) VALUES (%s, %s)', (user_name, uid))

  return render_template("user_create.html", user_name = user_name, uid = uid)


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
