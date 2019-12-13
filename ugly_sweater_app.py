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
import socket as sock
import RPi.GPIO as GPIO
import multiprocessing as mp
from threading import Thread
from flask_socketio import SocketIO
from flask import Flask, request, render_template, url_for

from timeit import timeit # debug

app = Flask(__name__)
socketio = SocketIO(app)

class led():

    def __init__(self, color, state, frequency, pin):
        self.color = color
        self.state = state
        self.frequency = frequency
        self.pin = pin

    def sleep(self):
        t_ = self.frequency
        if f_:
            return (1 / f_) / 2
        else:
            return None

    def turn_on(self):
        # consider trying on_=GPIO.output(self.pin, 1) in run function
        GPIO.output(self.pin, 1)

    def turn_off(self):
        GPIO.output(self.pin, 0)

    def run(self, sleep_=time.sleep):
        while True:
            f_ = self.frequency
            if f_:
                t_ = (1 / f_) / 2
                self.turn_on()
                sleep_(t_)
                self.turn_off()
                sleep_(t_)
            else:
                self.turn_off() # consider adding test and pass

    def start_run_thread(self):
        Thread(target=self.run, daemon=True).start()

    def get_state_json(self):
        # if frequency was set to 0 make sure state is 0
        if self.frequency == 0:
            self.state = 0
        else:
            self.state = 1
        # return new state as a json
        return {'color' : self.color,
                'state' : self.state,
                'freq' : self.frequency}

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

# def start_threads():
#     # starts threads in a seperate process
#
#     # set red thread's target function
#     red_thread = threading.Thread(target=control_red, daemon=True)
#     red_thread.start() # start red thread
#     # set green thread's target function
#     green_thread = threading.Thread(target=control_green, daemon=True)
#     green_thread.start() # start green thread
#     # set blue thread's target function
#     blue_thread = threading.Thread(target=control_blue, daemon=True)
#     blue_thread.start() # start blue thread
#     # # set white thread's target function
#     white_thread = threading.Thread(target=control_white, daemon=True)
#     white_thread.start() # start white thread

def control_red():
    # control red lights via pin 5 from dedicated thread

    # declare needed local variables
    pin = 5

    while True: # run as long as program is served
        # look for state change
        f = red['freq']
        # if frequency is non-zero light is on and blinked
        if f > 0:
            t = (1/f) / 2 # set sleep time
            GPIO.output(5, 1) # turn on
            time.sleep(t) # hold on
            GPIO.output(5, 0) # turn off
            time.sleep(t) # hold off
        else: # frequency is zero, light should be off
            GPIO.output(pin, 0) # ensure off

#
# def control_green():
#     # control green lights via pin 7 from dedicated thread
#
#     # declare needed local variables
#     pin = 7
#
#     while True: # run as long as program is served
#         # look for state change
#         f = green['freq']
#         # if frequency is non-zero light is on and blinked
#         if f > 0:
#             t = (1/f) / 2 # set sleep time
#             print("turn on:", timeit(f"{GPIO.output(pin, 1)}", number=1)) # turn on
#             print("sleep on:", timeit(f"time.sleep({t})", number=1)) # hold on
#             print("turn off:", timeit(f"{GPIO.output(pin, 0)}", number=1)) # turn off
#             print("sleep off:", timeit(f"time.sleep({t})", number=1)) # hold off
#         else: # frequency is zero, light should be off
#             GPIO.output(pin, 0) # ensure off
#
# def control_blue():
#     # control blue lights via pin 37 from dedicated thread
#
#     # declare needed local variables
#     pin = 37
#
#     while True: # run as long as program is served
#         # look for state change
#         f = blue['freq']
#         # if frequency is non-zero light is on and blinked
#         if f > 0:
#             t = (1/f) / 2 # set sleep time
#             GPIO.output(pin, 1) # turn on
#             time.sleep(t) # hold on
#             GPIO.output(pin, 0) # turn off
#             time.sleep(t) # hold off
#         else: # frequency is zero, light should be off
#             GPIO.output(pin, 0) # ensure off
#
# def control_white():
#     # control white lights via pin 35 from dedicated thread
#
#     global white
#
#     # declare needed local variables
#     pin = 35
#
#     while True: # run as long as program is served
#         # look for state change
#         f = white['freq']
#         # if frequency is non-zero light is on and blinked
#         if f > 0:
#             t = (1/f) / 2 # set sleep time
#             GPIO.output(pin, 1) # turn on
#             time.sleep(t) # hold on
#             GPIO.output(pin, 0) # turn off
#             time.sleep(t) # hold off
#         else: # frequency is zero, light should be off
#             GPIO.output(pin, 0) # ensure off


@app.route('/')
def serve_up_landing_page():
    # serve the landing page as root

    return render_template('index.html') # render appropriate html

@socketio.on('connect')
def process_connection():
    # send present state of requested color on new client connection

    # send red initialization state
    socketio.emit('red_init_state', red.get_state_json())
    # send green initialization state
    socketio.emit('green_init_state', green.get_state_json())
    # send blue initialization state
    socketio.emit('blue_init_state', blue.get_state_json())
    # send white initialization state
    socketio.emit('white_init_state', white.get_state_json())

@socketio.on('update_state')
def process_state_update(json):
    # process state update for requested color

    if json['color'] == 0: # if red changed
        # set red frequency
        red.frequency = json['freq']
        # send json of changes to all clients
        socketio.emit('change_of_state',
                        (red.get_state_json(), json['btn_tap']),
                        broadcast=True)

    if json['color'] == 1: # if green changed
        # set green frequency
        green.frequency = json['freq']
        # send change dict as json to all clients
        socketio.emit('change_of_state',
                        (green.get_state_json(), json['btn_tap']),
                        broadcast=True)

    if json['color'] == 2: # if blue changed
        # set blue frequency
        blue.frequency = json['freq']
        # send change dict as json to all clients
        socketio.emit('change_of_state',
                        (blue.get_state_json(), json['btn_tap']),
                        broadcast=True)

    if json['color'] == 3: # if white changed
        # set white frequency
        white.frequency = json['freq']
        # send change dict as json to all clients
        socketio.emit('change_of_state',
                        (white.get_state_json(), json['btn_tap']),
                        broadcast=True)

if __name__ == '__main__':

    # set GPIO initial state on startup
    set_gpio_on_startup()

    # set light states on server startup
    red = led(0, 0, 0, 5)
    green = led(1, 0, 0, 7)
    blue = led(2, 0, 0, 37)
    white = led(3, 0, 0, 35)

    # start threads
    #start_threads()

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
