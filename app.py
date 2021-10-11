import os
import json
from datetime import date

import random
from twilio.rest import Client
import http.client

from flask import Flask, render_template, request, session, jsonify, session, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session.__init__ import Session
import matplotlib.pyplot as plt
from io import BytesIO


app = Flask(__name__)
app.static_folder = 'static'


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

def calculateAge(birthDate):
    today = date.today()
    age = today.year - birthDate.year - \
        ((today.month, today.day) < (birthDate.month, birthDate.day))

    return age






def generateOTP():
    otp = random.randrange(100000, 1000000)
    return otp

@app.route("/", methods=["GET"])
def login():
    if session.get('login') is None or session.get('login') is "":
        session['login'] = ""
        return render_template("login.html")
    else:
        try:
            credentials = db.execute(
                "SELECT * FROM ADMINS WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
            return redirect("/admin_dash")
        except:
            return redirect("/dashboard")


@app.route("/login_back", methods = ["POST","GET"])
def login_back():
    if (session.get('login') is not None and session.get('login') is not ""):
        return redirect("/dashboard")
    
    aadhar = request.form.get('aadhar')
    pw = str(request.form.get('pw'))

    try:
        credentials = db.execute("SELECT * FROM AADHAR WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': aadhar}).fetchall()[0]
        password_chk = db.execute("SELECT AADHAR_NO FROM PASS_CRED WHERE AADHAR_NO = :SMTH AND password = crypt(:PW, password);", {'SMTH': aadhar, "PW":pw}).fetchall()[0][0]
    except:
        return render_template("error.html", message="Invalid credentials!")

    global otp
    otp = generateOTP()
    account_sid = 'AC1cf0738f673d21b26aa57a16d324ec30'
    auth_token = '59b9c8ce0f3995f2f7a2acd29ae144c5'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="\n\n==================\nYour aadhar otp is "+str(otp),
        from_='+18477371509',
        to=credentials[3]
    )
    print(otp)
    print(credentials)
    return render_template("otp_verif.html", credentials=credentials)



        
@app.route('/logverif/<string:aadhar>', methods=['POST'])
def logverif(aadhar):
    global otp
    if (session.get('login') is not None and session.get('login') is not ""):
        return redirect("/dashboard")

    answer = request.form.get('otp-no-login')
    if(str(otp) == str(answer)):
        session['login'] = str(aadhar)
        try:
            credentials = db.execute(
                "SELECT * FROM ADMINS WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
            return redirect("/admin_dash")
        except:
            return redirect("/dashboard")
    else:
        return render_template('error.html', message="Wrong OTP")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    try:
        redirect("/admin_dash")
    except:
        pass
    if (session.get('login') is not None and session.get('login') is not ""):
        credentials = db.execute(
            "SELECT * FROM AADHAR WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
        return render_template('homepage.html', message=session['login'], name=credentials[1])
    else:
        return render_template('error.html', message='Bad access')

@app.route('/aadharView/<string:aadhar>', methods=["GET"])
def aadharView(aadhar):
    if (session.get('login') is not None and session.get('login') is not ""):
        credentials = db.execute(
            "SELECT * FROM AADHAR WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
        return render_template('aadharView.html', credentials=credentials)
    else:
        return render_template('error.html', message='Bad access')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if (session.get('login') is not None and session.get('login') is not ""):
        credentials = db.execute(
            "SELECT * FROM AADHAR WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]

        return render_template('registertovote.html', credentials=credentials)
    else:
        return render_template('error.html', message='Bad access')

@app.route('/regback', methods=['POST', 'GET'])
def regback():
    if (session.get('login') is not None and session.get('login') is not ""):
        aadharNumber = str(session['login'])
        zone_id = str(request.form.get('zone-id'))
        status = str(0)
        lis = []
        for temp in db.execute("SELECT LOC FROM LOC_DIS;").fetchall():
            lis.append(temp[0])

        dob = db.execute("SELECT DOB FROM AADHAR WHERE AADHAR_NO LIKE :aad;", {
                         'aad': session['login']}).fetchall()[0][0]
        if(calculateAge(dob) < 18):
            return render_template('error.html', message="Minors cannot register")
        try:
            if (zone_id not in lis):
                return render_template('error.html', message="Invalid location")
            db.execute("INSERT INTO REGISTER VALUES (:aad,:zone,:stat);", {
                'aad': aadharNumber, 'zone': zone_id, 'stat': status})
            db.commit()
            return render_template('sucesspage.html', message='Done')
        except:
            return render_template('error.html', message='Can only register once!')
    else:
        return render_template('error.html', message='Bad access')

@app.route('/search', methods=['GET'])
def search():
    if (session.get('login') is not None and session.get('login') is not ""):
        aadharNumber = str(session['login'])
        global zone
        try:
            zone = db.execute(
                "SELECT ZONE_ID FROM REGISTER WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0][0]
        except:
            return render_template('error.html', message='First register')
        zone2 = db.execute(
            "SELECT DIS FROM LOC_DIS WHERE LOC LIKE :loc;", {'loc': zone}).fetchall()[0][0]
        mp = db.execute(
            "SELECT PARTY.PARTY_SYMBOL,CAND.CAND_IMG,PARTY.PARTY_NAME,AADHAR.FNAME,AADHAR.LNAME FROM CAND INNER JOIN PARTY ON CAND.PARTY_ID= PARTY.PARTY_ID INNER JOIN AADHAR ON AADHAR.AADHAR_NO = CAND.CAND_AADHAR WHERE ZONE_ID IN (:zone2);", {'zone2': zone2}).fetchall()
        mla = db.execute(
            "SELECT PARTY.PARTY_SYMBOL,CAND.CAND_IMG,PARTY.PARTY_NAME,AADHAR.FNAME,AADHAR.LNAME FROM CAND INNER JOIN PARTY ON CAND.PARTY_ID= PARTY.PARTY_ID INNER JOIN AADHAR ON AADHAR.AADHAR_NO = CAND.CAND_AADHAR WHERE ZONE_ID IN (:zone);", {'zone': zone}).fetchall()
        return render_template('search.html', mp=mp, mla=mla)
    else:
        return render_template('error.html', message='Bad access')


@app.route('/vote', methods=['GET'])
def vote():
    if (session.get('login') is not None and session.get('login') is not ""):

        try:
            zone = db.execute(
                "SELECT * FROM REGISTER WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
            status = zone[2]
            zone = zone[1]
        except:
            return render_template('error.html', message='First register')

        if(status == "1"):
            return render_template('error.html', message='Can only vote once')
        else:
            zone2 = db.execute(
                "SELECT DIS FROM LOC_DIS WHERE LOC LIKE :loc;", {'loc': zone}).fetchall()[0][0]

            mp = db.execute("SELECT PARTY.PARTY_SYMBOL,CAND.CAND_IMG,PARTY.PARTY_NAME,AADHAR.FNAME,AADHAR.LNAME, CAND.CAND_ID FROM CAND INNER JOIN PARTY ON CAND.PARTY_ID= PARTY.PARTY_ID INNER JOIN AADHAR ON AADHAR.AADHAR_NO = CAND.CAND_AADHAR WHERE ZONE_ID IN (:zone2);", {
                            'zone2': zone2}).fetchall()
            mla = db.execute("SELECT PARTY.PARTY_SYMBOL,CAND.CAND_IMG,PARTY.PARTY_NAME,AADHAR.FNAME,AADHAR.LNAME, CAND.CAND_ID FROM CAND INNER JOIN PARTY ON CAND.PARTY_ID= PARTY.PARTY_ID INNER JOIN AADHAR ON AADHAR.AADHAR_NO = CAND.CAND_AADHAR WHERE ZONE_ID IN (:zone);", {
                             'zone': zone}).fetchall()
            return render_template('votes.html', mp=mp, mla=mla)
    else:
        return render_template('error.html', message='Bad access')


@app.route('/voteback', methods=['POST'])
def voteback():
    pass
    ln = request.form['values'].split(",")
    cand1, cand2 = ln

    db.execute("BEGIN;")
    status = db.execute('SELECT VOTE_STATUS FROM REGISTER WHERE AADHAR_NO LIKE :aad', {
        'aad': session['login']}).fetchall()[0][0]
    print(status)
    if(status == "1"):
        return json.dumps("Failed")
    else:
        db.execute("UPDATE REGISTER SET VOTE_STATUS = 1 WHERE AADHAR_NO LIKE :aad;", {
            'aad': session['login']})
    db.execute("UPDATE CAND SET VOTES = VOTES+1 WHERE CAND_ID IN (:cand1,:cand2);",
               {'cand1': cand1, 'cand2': cand2})
    db.execute("COMMIT;")
    db.commit()
    return json.dumps("Successful")


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session['login'] = ''
    return redirect("/")

@app.route('/admin_dash', methods=['GET', 'POST'])
def admin_dash():
    if (session.get('login') is not None and session.get('login') is not ""):
        try:
            credentials = db.execute(
                "SELECT * FROM ADMINS WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
            return render_template('admin_login.html', message=session['login'], name="Admin")
        except:
            return render_template('admin_login.html', message=session['login'], name="Admin")
            # return redirect("/dashboard")
    else:
        return render_template('error.html', message='Bad access')

@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    pass
    if (session.get('login') is not None and session.get('login') is not ""):
        credentials = db.execute(
            "SELECT * FROM AADHAR WHERE AADHAR_NO LIKE :SMTH;", {'SMTH': session['login']}).fetchall()[0]
        return render_template('see-vote.html')
    else:
        return render_template('error.html', message='Bad access')


@app.route('/admin_search_back', methods=['POST'])
def admin_search_back():
    pass
    if (session.get('login') is not None and session.get('login') is not ""):
        aadharNumber = str(session['login'])
        zone_id = str(request.form.get('zone-id'))
        lis = []
        for temp in db.execute("SELECT LOC FROM LOC_DIS;").fetchall():
            lis.append(temp[0])
        if (zone_id not in lis):
            return render_template('error.html', message="Invalid location")
        session['location_admin'] = zone_id
        return redirect('/admin_view_vote')
    else:
        return render_template('error.html', message='Bad access')


@app.route('/admin_view_vote')
def admin_view_vote():
    pass
    if (session.get('login') is not None and session.get('login') is not ""):
        try:
            zone = session['location_admin']
            zone2 = db.execute(
                "SELECT DIS FROM LOC_DIS WHERE LOC LIKE :loc;", {'loc': zone}).fetchall()[0][0]
            mp = db.execute("SELECT PARTY.PARTY_SYMBOL,CAND.CAND_IMG,PARTY.PARTY_NAME,AADHAR.FNAME,AADHAR.LNAME, CAND.CAND_ID,CAND.VOTES FROM CAND INNER JOIN PARTY ON CAND.PARTY_ID= PARTY.PARTY_ID INNER JOIN AADHAR ON AADHAR.AADHAR_NO = CAND.CAND_AADHAR WHERE ZONE_ID IN (:zone2);", {
                            'zone2': zone2}).fetchall()
            mla = db.execute("SELECT PARTY.PARTY_SYMBOL,CAND.CAND_IMG,PARTY.PARTY_NAME,AADHAR.FNAME,AADHAR.LNAME, CAND.CAND_ID,CAND.VOTES FROM CAND INNER JOIN PARTY ON CAND.PARTY_ID= PARTY.PARTY_ID INNER JOIN AADHAR ON AADHAR.AADHAR_NO = CAND.CAND_AADHAR WHERE ZONE_ID IN (:zone);", {
                             'zone': zone}).fetchall()

            
            names = [mp[0][3]+" "+mp[0][4], mp[1][3]+" "+mp[1][4],  mla[0][3]+" "+mla[0][4], mla[1][3]+" "+mla[1][4] ]
            score = [mp[0][-1],mp[1][-1],mla[0][-1],mla[1][-1]]



            return render_template('view-search.html', mp=mp, mla=mla)
        except:
            return render_template('error.html', message='Bad access')
    else:
        return render_template('error.html', message='Bad access')

@app.route('/feedback')
def feedback():
    if (session.get('login') is not None and session.get('login') is not ""):
        try:
            lis = db.execute('SELECT * FROM FEEDBACKS;').fetchall()

            feed = []
            for feedback in lis:
                temp = []
                if(feedback[2] == 1):
                    temp.append("Anonymous(Verified)")
                else:
                    temp.append(db.execute('SELECT FNAME FROM AADHAR WHERE AADHAR_NO LIKE (:id)', {
                        'id': feedback[0]}).fetchall()[0][0])
                temp.append(feedback[1])
                feed.append(temp)

            return render_template('feedback.html', feedbacks=feed)
        except:
            return render_template('error.html', message='nah')
    else:
        return render_template('error.html', message='Bad access')


@app.route('/backback', methods=['GET', 'POST'])
def backback():
    if (session.get('login') is not None and session.get('login') is not ""):
        text = request.form.get('textplace')
        res = request.form.get('anym')
        if(res == "1"):
            temp = 1
        else:
            temp = 0
        print(temp)
        try:
            db.execute('INSERT INTO FEEDBACKS VALUES (:id,:text,:anym);', {
                       'id': session['login'], 'text': text, 'anym': temp})
            db.commit()
        except:
            return render_template('error.html', message='Can not give feedback twice.')
        return redirect("/feedback")
    else:
        return render_template('error.html', message='Bad access')



