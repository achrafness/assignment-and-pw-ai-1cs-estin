# create python code with flask render template minmax_tree.html
from flask import Flask, render_template
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('minimax_tree.html')
if __name__ == '__main__':
    app.run(debug=True, port=9333)
