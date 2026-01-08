from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/grooming", methods=["GET", "POST"])
def grooming():
    if request.method == "POST":
        with open("grooming_input.txt", "w") as f:
            for v in request.form.values():
                f.write(v + "\n")

        result = subprocess.check_output(
            ["python", "predict_grooming_effort.py"]
        ).decode()

        return render_template("result.html",
                               effort=result,
                               phase="Grooming")

    return render_template("grooming.html")

@app.route("/implementation", methods=["GET", "POST"])
def implementation():
    if request.method == "POST":
        with open("implementation_input.txt", "w") as f:
            for v in request.form.values():
                f.write(v + "\n")

        result = subprocess.check_output(
            ["python", "predict_implementation.py"]
        ).decode()

        return render_template("result.html",
                               effort=result,
                               phase="Implementation")

    return render_template("implementation.html")

if __name__ == "__main__":
    app.run(debug=True)
