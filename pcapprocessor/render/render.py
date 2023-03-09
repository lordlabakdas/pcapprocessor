from flask import Flask, render_template
import seaborn as sns
import pandas as pd

app = Flask(__name__)

@app.route('/viz')
def viz():

    return render_template('graph.html', viz_url='/')