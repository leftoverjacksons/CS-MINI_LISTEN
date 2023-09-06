from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pymysql
from sqlalchemy import text, create_engine
import re

# Initialize Flask and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://rtroy:dtrules1+@MJ072TPK:3306/esp32_test_data'
db = SQLAlchemy(app)

# Global variables for session labeling and device detection
current_label = None
new_device_detected = False

# Session Model
class Session(db.Model):
    session_id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(255), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    end_time = db.Column(db.DateTime, default=None)

# Check if a table exists
def table_exists(name):
    query = text(f"SHOW TABLES LIKE :table_name")
    return db.session.execute(query, {'table_name': name}).first() is not None

# Create a new table
def create_table(name):
    clean_name = re.sub('[^a-zA-Z0-9_]', '_', name)
    if not table_exists(clean_name):
        create_table_sql = text(f"""
            CREATE TABLE {clean_name} (
                data_point_id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hot_junction FLOAT,
                cold_junction FLOAT,
                pressure INT,
                switch_state VARCHAR(10)
            );
        """)
        db.session.execute(create_table_sql)

# Main Index Route
@app.route('/')
def index():
    return render_template('form.html', server_version="1.0.3")

# Data Reception Route
@app.route('/data', methods=['POST'])
def receive_data():
    global current_label, new_device_detected
    data = request.json
    if data.get('type') == 'handshake':
        new_device_detected = True
        return jsonify(status="awaiting label")
    else:
        if not current_label:
            return jsonify(status="no label provided"), 400
        table_name = "data_" + str(current_label)
        if not table_exists(table_name):
            create_table(table_name)
        
        # Insert received data into the table
        insert_data(table_name, data)
        return jsonify(status="data stored")

# Helper function to insert data into table
def insert_data(table_name, data):
    hot_junction = float(data.get('Hot Junction'))
    cold_junction = float(data.get('Cold Junction'))
    pressure = int(data.get('Pressure (RAW ADC)'))
    switch_state = data.get('Pressure Switch State')
    insert_sql = text(f"""
        INSERT INTO {table_name} (hot_junction, cold_junction, pressure, switch_state)
        VALUES (:hot_junction, :cold_junction, :pressure, :switch_state);
    """)
    params = {
        "hot_junction": hot_junction,
        "cold_junction": cold_junction,
        "pressure": pressure,
        "switch_state": switch_state
    }
    db.session.execute(insert_sql, params)
    db.session.commit()

# Set Session Label Route
@app.route('/set-label', methods=['POST'])
def set_label():
    global current_label
    current_label = request.json.get('label')
    new_session = Session(session_name=current_label)
    db.session.add(new_session)
    db.session.commit()
    table_name = "data_" + str(new_session.session_id)
    create_table(table_name)
    return jsonify(status="label set and table created")

# Check Device Route
@app.route('/check_device')
def check_device():
    global new_device_detected
    if new_device_detected:
        new_device_detected = False
        return jsonify(new_device=True), 200
    return jsonify(new_device=False), 200

# Get Table Names
@app.route('/api/tables', methods=['GET'])
def get_tables():
    query = text("SHOW TABLES")
    result = db.session.execute(query)
    tables = [row[0] for row in result if not row[0] == 'sessions']
    return jsonify({"tables": tables})

# Get Table Data
# Get Table Data
@app.route('/api/data', methods=['GET'])
def get_data():
    table = request.args.get('table')
    limit = request.args.get('limit', default=200, type=int)
    if table and table_exists(table):
        query = text(f"SELECT * FROM {table} ORDER BY data_point_id DESC LIMIT :limit")
        fetched_result = db.session.execute(query, {"limit": limit}).fetchall()

        # Debugging: Check what 'fetched_result' contains and write to file
        with open("debug_file.txt", "a") as f:
            f.write(f"Debug - Query Result: {fetched_result}\n")
        
        # Debug - Check row type and write to file
        for row in fetched_result:
            with open("debug_file.txt", "a") as f:
                f.write(f"Debug - Row Type: {type(row)}\n")
        
        # Assuming the table has columns named 'data_point_id', 'timestamp', 'hot_junction', 'cold_junction', 'pressure', 'switch_state'
        data = [{
            'data_point_id': row[0],
            'timestamp': row[1].strftime('%Y-%m-%d %H:%M:%S'),
            'hot_junction': row[2],
            'cold_junction': row[3],
            'pressure': row[4],
            'switch_state': row[5]
        } for row in fetched_result]

        return jsonify(data)
    return jsonify({"error": "Invalid table name"}), 400





# Graphing Route
@app.route('/graph')
def graph():
    return render_template('graph.html')

# Main Function
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
