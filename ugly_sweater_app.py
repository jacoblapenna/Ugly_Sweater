"""
this program is the workhorse for controlling GPIO on a raspberry pi
via a flask web app, the pi turns on and off lights attached to a
christmas sweater.

Pin mapping:

Red: GPIO3, pin 5
Green: GPIO4, pin 7
Ground (red and green): GND, pin 9
Blue: GPIO19, pin 37
White: GPIO26, pin 35
Ground (blue and white): GND, pin 39

Jacob Lapenna, 10/17/2019
"""

import time
import threading
import socket as sock
import RPi.GPIO as GPIO
from flask_socketio import SocketIO
from flask import Flask, request, render_template, url_for

app = Flask(__name__)
socketio = SocketIO(app)
chat_members = {}

def set_gpio_on_startup():

    GPIO.setmode(GPIO.BOARD) # set numbering scheme to board model
    GPIO.setwarnings(False) # ignore warnings

    # set initial states and expectations
    GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW) # red
    GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW) # green
    GPIO.setup(37, GPIO.OUT, initial=GPIO.LOW) # blue
    GPIO.setup(35, GPIO.OUT, initial=GPIO.LOW) # white

def get_ip_address():
    # get the server's IP on which to serve app
    # client can navigate to IP

    ip_address = '127.0.0.1'  # Default to localhost
    s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM) # setup a socket object
    try:
        s.connect(('1.1.1.1', 1))  # does not have to be reachable
        ip_address = s.getsockname()[0]
    except OSError:
        pass
    finally:
	    s.close()
    return ip_address

def control_red():
    # control red lights via pin 5 from dedicated thread

    # look at global state first
    global red

    # declare needed local variables
    color = red
    f = color['freq']
    b = color['state']
    pin = 5

    while True: # run as long as program is served
        # if state is on and frequency is blinked
        if b == 1 and 0 < f < 30:
            t = (1 / f) / 2 # set sleep time
            GPIO.output(pin, 1) # turn on
            time.sleep(t) # hold on
            GPIO.output(pin, 0) # turn off
            GPIO.sleep(t) # hold off
        # if frequency is solid on but pin is low
        elif GPIO.input(pin) == 0 and f == 30:
            GPIO.output(pin, 1) # turn on
        # if state is off but pin is high
        elif GPIO.input(pin) == 1 and b == 0:
            GPIO.output(pin, 0) # turn off
        # in all other cases
        else:
            color = red # hold and look for state change
            f = color['freq']
            b = color['state']

def control_green():
    # control green lights via pin 7 from dedicated thread
    pass

def control_blue():
    # control blue lights via pin 37 from dedicated thread
    pass

def control_white():
    # control white lights via pin 35 from dedicated thread
    pass

@app.route('/')
def serve_up_landing_page():
    # serve the landing page as root

    return render_template('index.html') # render appropriate html

@socketio.on('connect')
def process_connection():
    # send present state of requested color on new client connection

    socketio.emit('red_init_state', red) # send red initialization state
    socketio.emit('green_init_state', green) # send green initialization state
    socketio.emit('blue_init_state', blue) # send blue initialization state
    socketio.emit('white_init_state', white) # send white initialization state

@socketio.on('update_state')
def process_state_update(json):
    # process state update for requested color

    # declare variables as global
    global red, green, blue, white

    # declare helper function
    def build_json(color, frequency):
        if int(frequency) == 0: # if client turned light off
            # return new state with light off
            return {'color' : color, 'state' : 0, 'freq' : 0}
        else: # otherwise update with desired frequency
            # change state to new parameters
            return {'color' : color, 'state' : 1, 'freq' : int(frequency)}

    if json['color'] == 0: # if red changed
        # build dict describing change
        red = build_json(0, json['freq'])
        # send change dict as json to all clients
        socketio.emit('change_of_state', (red, json['btn_tap']), broadcast=True)
    if json['color'] == 1:
        # build dict describing change
        green = build_json(1, json['freq'])
        # send change dict as json to all clients
        socketio.emit('change_of_state', (green, json['btn_tap']), broadcast=True)
    if json['color'] == 2:
        # build dict describing change
        blue = build_json(2, json['freq'])
        # send change dict as json to all clients
        socketio.emit('change_of_state', (blue, json['btn_tap']), broadcast=True)
    if json['color'] == 3:
        # build dict describing change
        white = build_json(3, json['freq'])
        # send change dict as json to all clients
        socketio.emit('change_of_state', (white, json['btn_tap']), broadcast=True)

if __name__ == '__main__':

    # set GPIO initial state on startup
    set_gpio_on_startup()

    # set light states on server startup
    red = {'color' : 0, 'state' : 0, 'freq' : 0}
    green = {'color' : 1, 'state' : 0, 'freq' : 0}
    blue = {'color' : 2, 'state' : 0, 'freq' : 0}
    white = {'color' : 3, 'state' : 0, 'freq' : 0}

    # start control threads
    # set red thread's target function
    red_thread = threading.Thread(target=control_red)
    red_thread.start() # start red thread
    # set green thread's target function
    green_thread = threading.Thread(target=control_green)
    green_thread.start() # start green thread
    # set blue thread's target function
    blue_thread = threading.Thread(target=control_blue)
    blue_thread.start() # start blue thread
    # set white thread's target function
    white_thread = threading.Thread(target=control_white)
    white_thread.start() # start white thread


    # get ip address and serve app
    ip = get_ip_address()
    print("Attempting to serve page on %s:%d" % (ip, 31337))
    socketio.run(app,
                 host=ip,
                 port=31337,
                 use_reloader=True,
                 debug=False,
                 extra_files=['templates/index.html',
                              'templates/landing.html'])
