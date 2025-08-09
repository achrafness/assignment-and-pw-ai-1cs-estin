from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from csp_solver import CSPSolver

app = Flask(__name__)
app.secret_key = 'csp_timetable_scheduler'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_timetable():
    try:
        solver = CSPSolver()
        timetable = solver.solve()
        
        if timetable:
            return render_template('timetable.html', timetable=timetable)
        else:
            flash('Could not generate a valid timetable with the given constraints. Try relaxing some constraints.')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,port=3333)