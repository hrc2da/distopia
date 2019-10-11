from flask import Flask
import os
app = Flask(__name__)

@app.route("/")
def root():
    print(os.getcwd())
    return app.send_static_file("html/index.html")

if __name__ == "__main__":
    app.run()