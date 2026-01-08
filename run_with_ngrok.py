from pyngrok import ngrok
import subprocess
import time

# OPTIONAL: set token here once (recommended)
ngrok.set_auth_token("37y183Z4mzZJoUCk1Nw9C4lJySp_2qstwihGz1RtD5G5wA43F")

# Start Flask app
print("Starting Flask app...")
subprocess.Popen(["python", "app.py"])

# Give Flask time to start
time.sleep(3)

# Open ngrok tunnel
public_url = ngrok.connect(5000)
print("🌍 Your live website is here:")
print(public_url)
