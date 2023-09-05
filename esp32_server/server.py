from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pymysql
from sqlalchemy import text, create_engine

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://rtroy:dtrules1+@MJ072TPK:3306/esp32_test_data'
db = SQLAlchemy(app)
current_label = None
new_device_detected = False

class Session(db.Model):
    session_id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(255), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    end_time = db.Column(db.DateTime, default=None)

def table_exists(name):
    query = text(f"SHOW TABLES LIKE :table_name")
    return db.session.execute(query, {'table_name': name}).first() is not None



def create_table(name):
    if not table_exists(name):
        create_table_sql = text(f"""
            CREATE TABLE {name} (
                data_point_id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hot_junction FLOAT,
                cold_junction FLOAT,
                pressure INT,
                switch_state VARCHAR(10)
            );
        """)
        db.session.execute(create_table_sql)



@app.route('/')
def index():
    return render_template('form.html', server_version="1.0.3")

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
        
        return jsonify(status="data stored")

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

@app.route('/check_device')
def check_device():
    global new_device_detected
    if new_device_detected:
        new_device_detected = False
        return jsonify(new_device=True), 200
    return jsonify(new_device=False), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
