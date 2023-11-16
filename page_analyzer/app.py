from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def get_main_page():
    return render_template('main_page.html')
