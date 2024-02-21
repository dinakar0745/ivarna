from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Load data from the Excel file
excel_file = 'Events.xlsx'
df = pd.read_excel(excel_file)

# Define the upload folder
UPLOAD_FOLDER = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        roll_number = request.form['roll_number']
        return display_info(roll_number)
    elif request.method == 'GET' and 'roll_number' in request.args:
        roll_number = request.args['roll_number']
        return display_info(roll_number)

    return render_template('index.html')

@app.route('/info/<roll_number>')
def display_info(roll_number):
    user_data = get_user_data(roll_number)
    if user_data:
        return render_template('info.html', user_data=user_data)
    else:
        return "No user found with that roll number."

def get_user_data(roll_number):
    user_data = df[df['RollNumber'] == int(roll_number)]
    if not user_data.empty:
        event_columns = user_data.columns[2:]  # Select columns from the third column onwards
        events = [event for event in event_columns if not pd.isnull(user_data[event].iloc[0])]
        user_info = {
            'roll_number': user_data['RollNumber'].values[0],
            'name': user_data['Name'].values[0],
            'events': events[:6]  # Get up to 6 events
        }
        return user_info
    else:
        return None

USERS = {
    'dp': 'Welcome987*',
    'prem': 'prem',
    # Add more users as needed
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in USERS and USERS[username] == password:
        session['logged_in'] = True
        session['username'] = username  # Store username in session
        print("Logged in as: "+ username)
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login.html', error='Invalid credentials')
    
@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if session.get('logged_in'):
        if request.method == 'POST':
            file = request.files['file']
            if file.filename != '':
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
                update_excel(file.filename)
                return redirect(url_for('admin_dashboard'))
        
        # Filter out rows where all event columns are empty
        existing_data = df.dropna(subset=df.columns[2:], how='all').copy()

        return render_template('admin.html', existing_data=existing_data)
    else:
        return redirect(url_for('admin'))


def update_excel(filename):
    new_data = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    global df
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel(excel_file, index=False)

@app.route('/logout' , methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True, port=7000, host='0.0.0.0')

