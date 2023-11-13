from flask import Flask


app = Flask(__name__)


@app.route('/')
def greet():
    return '<p>Hello, World!<p>'
