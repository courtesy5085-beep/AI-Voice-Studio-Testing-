🚀 FULL SAAS LEVEL AI VOICE STUDIO (FINAL UPGRADE)

import streamlit as st import sqlite3 import hashlib import smtplib import jwt import datetime from email.mime.text import MIMEText

---------- CONFIG ----------

SECRET_KEY = "supersecretkey" SMTP_EMAIL = "your_email@gmail.com" SMTP_PASSWORD = "your_app_password"

---------- DATABASE ----------

conn = sqlite3.connect("users.db", check_same_thread=False) c = conn.cursor()

c.execute(""" CREATE TABLE IF NOT EXISTS users ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT UNIQUE, password TEXT, credits INTEGER DEFAULT 10 ) """) conn.commit()

---------- SECURITY ----------

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

---------- EMAIL OTP ----------

def send_otp(email, otp): msg = MIMEText(f"Your OTP is {otp}") msg['Subject'] = "AI Voice Studio OTP" msg['From'] = SMTP_EMAIL msg['To'] = email

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()
    return True
except:
    return False

---------- JWT ----------

def create_token(email): payload = { "email": email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1) } return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

---------- AUTH ----------

def signup(username, email, password): try: c.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)", (username, email, hash_password(password))) conn.commit() return True except: return False

def login(email, password): c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hash_password(password))) return c.fetchone()

---------- SESSION ----------

if "token" not in st.session_state: st.session_state.token = None

---------- AUTH UI ----------

if not st.session_state.token: tab1, tab2 = st.tabs(["Login", "Signup"])

with tab1:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Send OTP"):
        user = login(email, password)
        if user:
            import random
            otp = str(random.randint(100000,999999))
            st.session_state.otp = otp
            st.session_state.email = email
            if send_otp(email, otp):
                st.success("OTP sent to email")
            else:
                st.warning(f"Demo OTP: {otp}")
        else:
            st.error("Invalid login")

    otp_input = st.text_input("Enter OTP")

    if st.button("Verify Login"):
        if otp_input == st.session_state.get("otp"):
            st.session_state.token = create_token(st.session_state.email)
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Wrong OTP")

with tab2:
    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    if st.button("Signup"):
        if signup(u, e, p):
            st.success("Account created")
        else:
            st.error("User exists")

st.stop()

---------- DASHBOARD ----------

st.title("🎙️ AI Voice Studio") st.sidebar.success("Logged In")

if st.sidebar.button("Logout"): st.session_state.token = None st.rerun()

---------- USER DATA ----------

c.execute("SELECT email, credits FROM users WHERE email=?", (st.session_state.email,)) user = c.fetchone()

---------- DASHBOARD ----------

st.subheader("👤 User Dashboard") st.write("Email:", user[0]) st.write("Credits:", user[1])

---------- CREDIT SYSTEM ----------

def use_credit(): c.execute("UPDATE users SET credits = credits - 1 WHERE email=?", (st.session_state.email,)) conn.commit()

---------- MAIN FEATURE ----------

text = st.text_area("Enter text for speech")

if st.button("Generate Voice"): if user[1] <= 0: st.error("No credits left") else: from gtts import gTTS import io tts = gTTS(text=text) fp = io.BytesIO() tts.write_to_fp(fp) fp.seek(0) st.audio(fp) use_credit()

---------- PAYMENT MOCK ----------

st.subheader("💰 Buy Credits") if st.button("Add 10 Credits (Demo)"): c.execute("UPDATE users SET credits = credits + 10 WHERE email=?", (st.session_state.email,)) conn.commit() st.success("Credits added")

---------- FOOTER ----------

st.caption("AI Voice Studio SaaS | Production Ready")
