from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import execute_query
from config import Config
import time

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# User Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username exists
        user = execute_query(
            "SELECT * FROM users WHERE username = %s", 
            (username,), 
            fetch_one=True
        )
        
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        # Hash password and create user
        password_hash = generate_password_hash(password)
        execute_query(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = execute_query(
            "SELECT * FROM users WHERE username = %s", 
            (username,), 
            fetch_one=True
        )
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Main Application Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's devices
    devices = execute_query(
        "SELECT * FROM devices WHERE user_id = %s",
        (session['user_id'],)
    )
    
    # Get latest data for each device
    device_data = []
    if devices:
        for device in devices:
            data = execute_query(
                """SELECT * FROM device_data 
                WHERE device_id = %s 
                ORDER BY timestamp DESC LIMIT 1""",
                (device['device_id'],),
                fetch_one=True
            )
            
            led_state = execute_query(
                """SELECT * FROM led_commands 
                WHERE device_id = %s 
                ORDER BY timestamp DESC LIMIT 1""",
                (device['device_id'],),
                fetch_one=True
            )
            
            device_data.append({
                'device_id': device['device_id'],
                'button_state': data['button_state'] if data else False,
                'led_state': led_state['led_state'] if led_state else False
            })
    
    return render_template('index.html', devices=device_data)

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        device_id = request.form['device_id']
        
        # Check if device exists
        device = execute_query(
            "SELECT * FROM devices WHERE device_id = %s",
            (device_id,),
            fetch_one=True
        )
        
        if device:
            flash('Device ID already exists', 'danger')
        else:
            execute_query(
                "INSERT INTO devices (user_id, device_id) VALUES (%s, %s)",
                (session['user_id'], device_id)
            )
            flash('Device added successfully!', 'success')
            return redirect(url_for('index'))
    
    return render_template('add_device.html')

@app.route('/toggle_led/<device_id>')
def toggle_led(device_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verify user owns this device
    device = execute_query(
        "SELECT * FROM devices WHERE device_id = %s AND user_id = %s",
        (device_id, session['user_id']),
        fetch_one=True
    )
    
    if not device:
        flash('Device not found', 'danger')
        return redirect(url_for('index'))
    
    # Get current LED state
    led_state = execute_query(
        """SELECT * FROM led_commands 
        WHERE device_id = %s 
        ORDER BY timestamp DESC LIMIT 1""",
        (device_id,),
        fetch_one=True
    )
    
    new_state = not led_state['led_state'] if led_state else True
    
    # Store new LED state
    execute_query(
        "INSERT INTO led_commands (device_id, led_state) VALUES (%s, %s)",
        (device_id, new_state)
    )
    
    flash(f'LED state changed to {"ON" if new_state else "OFF"}', 'success')
    return redirect(url_for('index'))

# API Endpoints for ESP32
@app.route('/api/device_data', methods=['POST'])
def receive_device_data():
    data = request.json
    device_id = data.get('device_id')
    button_state = data.get('button_state')
    
    if not device_id or button_state is None:
        return jsonify({'error': 'Missing device_id or button_state'}), 400
    
    # Verify device exists
    device = execute_query(
        "SELECT * FROM devices WHERE device_id = %s",
        (device_id,),
        fetch_one=True
    )
    
    if not device:
        return jsonify({'error': 'Device not registered'}), 404
    
    # Store button state
    execute_query(
        "INSERT INTO device_data (device_id, button_state) VALUES (%s, %s)",
        (device_id, bool(button_state))
    )
    
    return jsonify({'status': 'success'}), 200

@app.route('/api/get_led_state')
def get_led_state():
    device_id = request.args.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'Missing device_id'}), 400
    
    # Get latest LED command
    led_state = execute_query(
        """SELECT * FROM led_commands 
        WHERE device_id = %s 
        ORDER BY timestamp DESC LIMIT 1""",
        (device_id,),
        fetch_one=True
    )
    
    if led_state:
        return jsonify({'led_state': 'on' if led_state['led_state'] else 'off'})
    else:
        return jsonify({'led_state': 'off'})

if __name__ == '__main__':
    app.run(debug=True)