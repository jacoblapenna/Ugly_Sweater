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

    def turn_on(self):
        # consider trying on_=GPIO.output(self.pin, 1) in run function
        GPIO.output(self.pin, 1)

    def turn_off(self):
        GPIO.output(self.pin, 0)

    def run(self, sleep_=time.sleep):
        while True:
            f_ = self.frequency
            if f_ == 30:
                self.turn_on()
            elif f_:
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
        red.frequency = int(json['freq'])
        # send json of changes to all clients
        socketio.emit('change_of_state',
                        (red.get_state_json(), json['btn_tap']),
                        broadcast=True)

    if json['color'] == 1: # if green changed
        # set green frequency
        green.frequency = int(json['freq'])
        # send change dict as json to all clients
        socketio.emit('change_of_state',
                        (green.get_state_json(), json['btn_tap']),
                        broadcast=True)

    if json['color'] == 2: # if blue changed
        # set blue frequency
        blue.frequency = int(json['freq'])
        # send change dict as json to all clients
        socketio.emit('change_of_state',
                        (blue.get_state_json(), json['btn_tap']),
                        broadcast=True)

    if json['color'] == 3: # if white changed
        # set white frequency
        white.frequency = int(json['freq'])
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
    red.start_run_thread()
    green.start_run_thread()
    blue.start_run_thread()
    white.start_run_thread()

    # get ip address and serve app
    ip = get_ip_address()
    print("Attempting to serve page on %s:%d" % (ip, 31337))
    socketio.run(app,
                 host='0.0.0.0',
                 port=80,
                 use_reloader=True,
                 debug=False,
                 extra_files=['templates/index.html',
                              'templates/landing.html'])
