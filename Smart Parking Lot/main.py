import board
import busio
from digitalio import DigitalInOut, Direction
import adafruit_fingerprint
import random

import serial
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from sqlalchemy.orm import sessionmaker
from flask import Flask, request, flash, session, url_for, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import time
from datetime import datetime
#buat cuaca
import os
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class users(db.Model):
    text = db.Column(db.String)
    id = db.Column(db.Integer, primary_key=True)

class waktu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    datang = db.Column(db.DateTime)
    poin = db.Column(db.Integer)
    
class kepsek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pulangkepsek = db.Column(db.DateTime)

class guru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pulangguru = db.Column(db.DateTime)
    
db.create_all()


###############################################################
GPIO.setmode(GPIO.BCM)
reader = SimpleMFRC522()
GPIO.setwarnings(False)
#
GPIO.setup(21, GPIO.OUT)
GPIO.output(21, GPIO.LOW)

###############################################################

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route('/loginProses', methods=['POST'])
def proses_login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if (user.password != password):
        flash('Invalid username or password!', 'danger')
        return redirect(url_for('login'))

    session['username'] = user.name
    return redirect(url_for('dashboard'))

@app.route('/registerProses', methods=['POST'])
def proses_register():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('This email already exists in database', 'secondary')
        return redirect(url_for('login'))

    new_user = User(email=email, name=name, password=password)

    db.session.add(new_user)
    db.session.commit()
    flash("Email registered", 'secondary')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out!", 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    dt=waktu.query.all()
    kpl=kepsek.query.all()
    gpl=guru.query.all()

    return render_template('index7.html', dt=dt, kpl=kpl, gpl=gpl)

@app.route('/veriflogin')
def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_fast_search() != adafruit_fingerprint.OK:
        return False
    return True


@app.route('/fungsioner')
def enroll_finger():
    location = random.randint(5, 127)
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            pass
        else:
            pass

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            elif i == adafruit_fingerprint.NOFINGER:
                pass
            elif i == adafruit_fingerprint.IMAGEFAIL:
                flash("Imaging error")
                return False
            else:
                flash("Other error")
                return False

        
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            pass
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                flash("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                flash("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                flash("Image invalid")
            else:
                flash("Other error")
            return False

        if fingerimg == 1:
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        pass
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            flash("Prints did not match")
        else:
            flash("Other error")
        return False

    
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        flash("Stored in template %i" % location)
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            flash("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            flash("Flash storage error")
        else:
            flash("Other error")
        return False

    return True


@app.route('/find')
def find():
    if get_fingerprint():
        flash("Detected, template number %i" % finger.finger_id)
        return render_template('find.html', user=User.query.all())
    else:
        flash('Finger not found')
        return render_template('find.html', user=User.query.all())


@app.route('/enrollf')
def enrollf():
    if enroll_finger():
        return render_template('enroll.html', user=User.query.all())
    else:
        flash('Failed, try again')
        return render_template('enroll.html', user=User.query.all())


@app.route('/del')
def yyy():
    return render_template('delete.html', user=User.query.all())


@app.route('/delete', methods=['POST'])
def delete():
    if finger.delete_model(int(request.form.get('template'))) == adafruit_fingerprint.OK:
        flash("Deleted!")
    else:
        flash("Failed to delete")

    return render_template('delete.html', user=User.query.all())


@app.route("/fingerprint")
def control():
    return render_template('control.html')

@app.route("/rfid")
def rfid():
    return render_template('control2.html')


#ini buat daftar rfid
@app.route('/regis')
def regis():
    return render_template('regis.html')

#ini buat daftar rfid
@app.route('/daftar', methods=['POST'])
def daftar():
    #pakai global variabel
    global users
    text = request.form.get('text')
    reader.write(text)
    id, nm = reader.read()
    new_user = users(text=text, id=id)

    db.session.add(new_user)
    db.session.commit()
    
    flash("Success")
    return render_template('regis.html')

#ini buat simulasi buka gerbang 
@app.route('/scan')
def parkir():
    return render_template('scan.html', lampu = GPIO.input(21))

#ini buat simulasi buka gerbang
@app.route('/buka')
def buka():
    #pakai global variabel
    global users
    id, text = reader.read()
    users = users.query.filter_by(id=id).first()
    if not users:
        return render_template('scan.html', lampu = GPIO.input(21))
    else:
        GPIO.output(21, GPIO.HIGH)
        time.sleep(3)
        GPIO.output(21, GPIO.LOW)
        #memasukkan waktu kedatangan kedalam database
        datang_time = datetime.now()
        if datang_time.hour < 07.00:
            poin = 1
        elif datang_time.hour < 08.00:
            poin = 0.5
        elif datang_time.hour >= 08.00:
            poin = 0
        user=waktu(text=text, datang=datang_time, poin=poin)
        db.session.add(user)
        db.session.commit()
        flash("Dibuka oleh %s" % text)
        return render_template('scan.html', lampu = GPIO.input(21))
    
#ini buat simulasi pulang
@app.route('/pulangkepsek')
def pulangkepsek():
    if get_fingerprint():
        pulangkepsek_time = datetime.now()
        user=kepsek(pulangkepsek=pulangkepsek_time)
        db.session.add(user)
        db.session.commit()
        return render_template('scan.html')
    else:
        return render_template('scan.html')

@app.route('/pulangguru')
def pulangguru():
    if get_fingerprint():
        pulangguru_time = datetime.now()
        user=guru(pulangguru=pulangguru_time)
        db.session.add(user)
        db.session.commit()
        return render_template('scan.html')
    else:
        return render_template('scan.html')
    
#ini buat fitur rfid control rfid find tag
@app.route('/baca')
def baca():
    global users
    id, text = reader.read()
    users = users.query.filter_by(id=id).first()
    if not users:
        flash("User not available")
        return render_template('findrfid.html')
    else:
        flash("User %s" % text)
        return render_template('findrfid.html')

@app.route('/graph')
def grafik():
    pt = waktu.query.all()
    text = []
    poin = []
    
    for amounts in pt:
        poin.append(amounts.poin)
        text.append(amounts.text)
    
    return render_template('grafik.html', pt=pt, text=text, poin=poin)
    
if __name__ == "__main__":
    app.run(host='192.168.101.182')
