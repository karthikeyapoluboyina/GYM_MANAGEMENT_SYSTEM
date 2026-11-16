from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
import datetime
from config import Config

app = Flask(__name__)

# Database connection
def get_db_connection():
    """Create and return a database connection"""
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        port=Config.MYSQL_PORT
    )
    return conn

# Utility function to convert MySQL rows to dictionaries
def row_to_dict(cursor, row):
    """Convert MySQL row to dictionary"""
    return dict(zip([column[0] for column in cursor.description], row))

# Routes
@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page with statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get stats for dashboard
    stats = {}
    
    # Total members
    cursor.execute("SELECT COUNT(*) FROM members")
    stats['total_members'] = cursor.fetchone()[0]
    
    # Total trainers
    cursor.execute("SELECT COUNT(*) FROM trainers")
    stats['total_trainers'] = cursor.fetchone()[0]
    
    # Today's attendance
    today = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute(f"SELECT COUNT(*) FROM attendance WHERE DATE(check_in_time) = '{today}'")
    stats['today_attendance'] = cursor.fetchone()[0]
    
    # Members per plan
    cursor.execute("""
        SELECT p.name, COUNT(m.id) as count 
        FROM plans p
        LEFT JOIN members m ON p.id = m.plan_id
        GROUP BY p.id
    """)
    stats['members_per_plan'] = []
    for row in cursor.fetchall():
        stats['members_per_plan'].append({
            'plan': row[0],
            'count': row[1]
        })
    
    # Recent members
    cursor.execute("""
        SELECT id, name, email, join_date
        FROM members
        ORDER BY join_date DESC
        LIMIT 5
    """)
    stats['recent_members'] = []
    for row in cursor.fetchall():
        stats['recent_members'].append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'join_date': row[3].strftime('%Y-%m-%d')
        })
    
    # Recent check-ins
    cursor.execute("""
        SELECT a.id, m.name, a.check_in_time
        FROM attendance a
        JOIN members m ON a.member_id = m.id
        ORDER BY a.check_in_time DESC
        LIMIT 5
    """)
    stats['recent_checkins'] = []
    for row in cursor.fetchall():
        stats['recent_checkins'].append({
            'id': row[0],
            'name': row[1],
            'time': row[2].strftime('%Y-%m-%d %H:%M:%S')
        })
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', stats=stats)

# Members routes
@app.route('/members')
def view_members():
    """Render the members page"""
    return render_template('members.html')

@app.route('/api/members', methods=['GET'])
def get_members():
    """API to get all members"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT m.id, m.name, m.email, m.phone, m.join_date, 
               m.address, m.emergency_contact, m.notes, p.name as plan_name
        FROM members m
        LEFT JOIN plans p ON m.plan_id = p.id
    """
    
    # Add search functionality
    search = request.args.get('search', '')
    if search:
        query += f" WHERE m.name LIKE '%{search}%' OR m.email LIKE '%{search}%' OR m.phone LIKE '%{search}%'"
    
    query += " ORDER BY m.id DESC"
    
    cursor.execute(query)
    members = []
    for row in cursor.fetchall():
        member = {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'join_date': row[4].strftime('%Y-%m-%d') if row[4] else None,
            'address': row[5],
            'emergency_contact': row[6],
            'notes': row[7],
            'plan_name': row[8]
        }
        members.append(member)
    
    cursor.close()
    conn.close()
    
    return jsonify(members)

@app.route('/api/members', methods=['POST'])
def add_member():
    """API to add a new member"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate required fields
    required_fields = ['name', 'email', 'phone', 'join_date', 'plan_id']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Field {field} is required'}), 400
    
    # Check if email already exists
    cursor.execute("SELECT id FROM members WHERE email = %s", (data['email'],))
    if cursor.fetchone():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        query = """
            INSERT INTO members (name, email, phone, join_date, plan_id, address, emergency_contact, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['name'],
            data['email'],
            data['phone'],
            data['join_date'],
            data['plan_id'],
            data.get('address', ''),
            data.get('emergency_contact', ''),
            data.get('notes', '')
        ))
        conn.commit()
        
        # Get the ID of the new member
        new_id = cursor.lastrowid
        
        return jsonify({'success': True, 'id': new_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """API to update a member"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if member exists
        cursor.execute("SELECT id FROM members WHERE id = %s", (member_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Member not found'}), 404
        
        # Check email uniqueness if email is being updated
        if 'email' in data:
            cursor.execute("SELECT id FROM members WHERE email = %s AND id != %s", (data['email'], member_id))
            if cursor.fetchone():
                return jsonify({'error': 'Email already exists'}), 400
        
        # Build update query dynamically based on provided fields
        fields = []
        values = []
        
        update_fields = ['name', 'email', 'phone', 'join_date', 'plan_id', 'address', 'emergency_contact', 'notes']
        for field in update_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        query = f"UPDATE members SET {', '.join(fields)} WHERE id = %s"
        values.append(member_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    """API to delete a member"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if member exists
        cursor.execute("SELECT id FROM members WHERE id = %s", (member_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Member not found'}), 404
        
        # Delete member
        cursor.execute("DELETE FROM members WHERE id = %s", (member_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    """API to get a specific member"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT m.id, m.name, m.email, m.phone, m.join_date, 
                   m.plan_id, m.address, m.emergency_contact, m.notes,
                   p.name as plan_name
            FROM members m
            LEFT JOIN plans p ON m.plan_id = p.id
            WHERE m.id = %s
        """
        cursor.execute(query, (member_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Member not found'}), 404
        
        member = {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'join_date': row[4].strftime('%Y-%m-%d') if row[4] else None,
            'plan_id': row[5],
            'address': row[6],
            'emergency_contact': row[7],
            'notes': row[8],
            'plan_name': row[9]
        }
        
        return jsonify(member)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Trainers routes
@app.route('/trainers')
def view_trainers():
    """Render the trainers page"""
    return render_template('trainers.html')

@app.route('/api/trainers', methods=['GET'])
def get_trainers():
    """API to get all trainers"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, name, specialty, email, phone, hire_date, bio
        FROM trainers
    """
    
    # Add search functionality
    search = request.args.get('search', '')
    if search:
        query += f" WHERE name LIKE '%{search}%' OR specialty LIKE '%{search}%' OR email LIKE '%{search}%'"
    
    query += " ORDER BY id DESC"
    
    cursor.execute(query)
    trainers = []
    for row in cursor.fetchall():
        trainer = {
            'id': row[0],
            'name': row[1],
            'specialty': row[2],
            'email': row[3],
            'phone': row[4],
            'hire_date': row[5].strftime('%Y-%m-%d') if row[5] else None,
            'bio': row[6]
        }
        trainers.append(trainer)
    
    cursor.close()
    conn.close()
    
    return jsonify(trainers)

@app.route('/api/trainers', methods=['POST'])
def add_trainer():
    """API to add a new trainer"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate required fields
    required_fields = ['name', 'specialty', 'email', 'phone', 'hire_date']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Field {field} is required'}), 400
    
    # Check if email already exists
    cursor.execute("SELECT id FROM trainers WHERE email = %s", (data['email'],))
    if cursor.fetchone():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        query = """
            INSERT INTO trainers (name, specialty, email, phone, hire_date, bio)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['name'],
            data['specialty'],
            data['email'],
            data['phone'],
            data['hire_date'],
            data.get('bio', '')
        ))
        conn.commit()
        
        # Get the ID of the new trainer
        new_id = cursor.lastrowid
        
        return jsonify({'success': True, 'id': new_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/trainers/<int:trainer_id>', methods=['PUT'])
def update_trainer(trainer_id):
    """API to update a trainer"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if trainer exists
        cursor.execute("SELECT id FROM trainers WHERE id = %s", (trainer_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Trainer not found'}), 404
        
        # Check email uniqueness if email is being updated
        if 'email' in data:
            cursor.execute("SELECT id FROM trainers WHERE email = %s AND id != %s", (data['email'], trainer_id))
            if cursor.fetchone():
                return jsonify({'error': 'Email already exists'}), 400
        
        # Build update query dynamically based on provided fields
        fields = []
        values = []
        
        update_fields = ['name', 'specialty', 'email', 'phone', 'hire_date', 'bio']
        for field in update_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        query = f"UPDATE trainers SET {', '.join(fields)} WHERE id = %s"
        values.append(trainer_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/trainers/<int:trainer_id>', methods=['DELETE'])
def delete_trainer(trainer_id):
    """API to delete a trainer"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if trainer exists
        cursor.execute("SELECT id FROM trainers WHERE id = %s", (trainer_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Trainer not found'}), 404
        
        # Delete trainer
        cursor.execute("DELETE FROM trainers WHERE id = %s", (trainer_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/trainers/<int:trainer_id>', methods=['GET'])
def get_trainer(trainer_id):
    """API to get a specific trainer"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT id, name, specialty, email, phone, hire_date, bio
            FROM trainers
            WHERE id = %s
        """
        cursor.execute(query, (trainer_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Trainer not found'}), 404
        
        trainer = {
            'id': row[0],
            'name': row[1],
            'specialty': row[2],
            'email': row[3],
            'phone': row[4],
            'hire_date': row[5].strftime('%Y-%m-%d') if row[5] else None,
            'bio': row[6]
        }
        
        return jsonify(trainer)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Plans routes
@app.route('/plans')
def view_plans():
    """Render the plans page"""
    return render_template('plans.html')

@app.route('/api/plans', methods=['GET'])
def get_plans():
    """API to get all plans"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, name, duration_months, price, description
        FROM plans
    """
    
    # Add search functionality
    search = request.args.get('search', '')
    if search:
        query += f" WHERE name LIKE '%{search}%' OR description LIKE '%{search}%'"
    
    query += " ORDER BY price ASC"
    
    cursor.execute(query)
    plans = []
    for row in cursor.fetchall():
        plan = {
            'id': row[0],
            'name': row[1],
            'duration_months': row[2],
            'price': float(row[3]),
            'description': row[4]
        }
        plans.append(plan)
    
    cursor.close()
    conn.close()
    
    return jsonify(plans)

@app.route('/api/plans', methods=['POST'])
def add_plan():
    """API to add a new plan"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate required fields
    required_fields = ['name', 'duration_months', 'price']
    for field in required_fields:
        if field not in data or data[field] == '':
            return jsonify({'error': f'Field {field} is required'}), 400
    
    try:
        query = """
            INSERT INTO plans (name, duration_months, price, description)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['name'],
            data['duration_months'],
            data['price'],
            data.get('description', '')
        ))
        conn.commit()
        
        # Get the ID of the new plan
        new_id = cursor.lastrowid
        
        return jsonify({'success': True, 'id': new_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/plans/<int:plan_id>', methods=['PUT'])
def update_plan(plan_id):
    """API to update a plan"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if plan exists
        cursor.execute("SELECT id FROM plans WHERE id = %s", (plan_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Plan not found'}), 404
        
        # Build update query dynamically based on provided fields
        fields = []
        values = []
        
        update_fields = ['name', 'duration_months', 'price', 'description']
        for field in update_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        query = f"UPDATE plans SET {', '.join(fields)} WHERE id = %s"
        values.append(plan_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/plans/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    """API to delete a plan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if plan exists
        cursor.execute("SELECT id FROM plans WHERE id = %s", (plan_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Plan not found'}), 404
        
        # Check if plan is being used by any members
        cursor.execute("SELECT COUNT(*) FROM members WHERE plan_id = %s", (plan_id,))
        if cursor.fetchone()[0] > 0:
            return jsonify({'error': 'Cannot delete plan that is assigned to members'}), 400
        
        # Delete plan
        cursor.execute("DELETE FROM plans WHERE id = %s", (plan_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/plans/<int:plan_id>', methods=['GET'])
def get_plan(plan_id):
    """API to get a specific plan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT id, name, duration_months, price, description
            FROM plans
            WHERE id = %s
        """
        cursor.execute(query, (plan_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Plan not found'}), 404
        
        plan = {
            'id': row[0],
            'name': row[1],
            'duration_months': row[2],
            'price': float(row[3]),
            'description': row[4]
        }
        
        return jsonify(plan)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Attendance routes
@app.route('/attendance')
def view_attendance():
    """Render the attendance page"""
    return render_template('attendance.html')

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """API to get attendance records"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get date filter parameters
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    member_id = request.args.get('member_id', '')
    
    query = """
        SELECT a.id, a.member_id, m.name as member_name, a.check_in_time, a.check_out_time, a.notes
        FROM attendance a
        JOIN members m ON a.member_id = m.id
    """
    
    where_clauses = []
    params = []
    
    if date_from:
        where_clauses.append("DATE(a.check_in_time) >= %s")
        params.append(date_from)
    
    if date_to:
        where_clauses.append("DATE(a.check_in_time) <= %s")
        params.append(date_to)
    
    if member_id:
        where_clauses.append("a.member_id = %s")
        params.append(member_id)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY a.check_in_time DESC"
    
    cursor.execute(query, params)
    attendance_records = []
    for row in cursor.fetchall():
        record = {
            'id': row[0],
            'member_id': row[1],
            'member_name': row[2],
            'check_in_time': row[3].strftime('%Y-%m-%d %H:%M:%S'),
            'check_out_time': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None,
            'notes': row[5]
        }
        attendance_records.append(record)
    
    cursor.close()
    conn.close()
    
    return jsonify(attendance_records)

@app.route('/api/attendance', methods=['POST'])
def add_attendance():
    """API to add a new attendance record"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate required fields
    if 'member_id' not in data or not data['member_id']:
        return jsonify({'error': 'Member ID is required'}), 400
    
    try:
        # Check if member exists
        cursor.execute("SELECT id FROM members WHERE id = %s", (data['member_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Member not found'}), 404
        
        # Set check-in time to current time if not provided
        check_in_time = data.get('check_in_time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        query = """
            INSERT INTO attendance (member_id, check_in_time, check_out_time, notes)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['member_id'],
            check_in_time,
            data.get('check_out_time'),
            data.get('notes', '')
        ))
        conn.commit()
        
        # Get the ID of the new attendance record
        new_id = cursor.lastrowid
        
        return jsonify({'success': True, 'id': new_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/attendance/<int:attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    """API to update an attendance record"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if attendance record exists
        cursor.execute("SELECT id FROM attendance WHERE id = %s", (attendance_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Attendance record not found'}), 404
        
        # Build update query dynamically based on provided fields
        fields = []
        values = []
        
        update_fields = ['member_id', 'check_in_time', 'check_out_time', 'notes']
        for field in update_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        query = f"UPDATE attendance SET {', '.join(fields)} WHERE id = %s"
        values.append(attendance_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    """API to delete an attendance record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if attendance record exists
        cursor.execute("SELECT id FROM attendance WHERE id = %s", (attendance_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Attendance record not found'}), 404
        
        # Delete attendance record
        cursor.execute("DELETE FROM attendance WHERE id = %s", (attendance_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Assignments routes
@app.route('/api/assignments', methods=['GET'])
def get_assignments():
    """API to get trainer assignments"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    member_id = request.args.get('member_id', '')
    trainer_id = request.args.get('trainer_id', '')
    
    query = """
        SELECT a.id, a.member_id, m.name as member_name, a.trainer_id, t.name as trainer_name,
               a.start_date, a.end_date, a.notes
        FROM assignments a
        JOIN members m ON a.member_id = m.id
        JOIN trainers t ON a.trainer_id = t.id
    """
    
    where_clauses = []
    params = []
    
    if member_id:
        where_clauses.append("a.member_id = %s")
        params.append(member_id)
    
    if trainer_id:
        where_clauses.append("a.trainer_id = %s")
        params.append(trainer_id)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY a.start_date DESC"
    
    cursor.execute(query, params)
    assignments = []
    for row in cursor.fetchall():
        assignment = {
            'id': row[0],
            'member_id': row[1],
            'member_name': row[2],
            'trainer_id': row[3],
            'trainer_name': row[4],
            'start_date': row[5].strftime('%Y-%m-%d') if row[5] else None,
            'end_date': row[6].strftime('%Y-%m-%d') if row[6] else None,
            'notes': row[7]
        }
        assignments.append(assignment)
    
    cursor.close()
    conn.close()
    
    return jsonify(assignments)

@app.route('/api/assignments', methods=['POST'])
def add_assignment():
    """API to add a new trainer assignment"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate required fields
    required_fields = ['member_id', 'trainer_id', 'start_date']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Field {field} is required'}), 400
    
    try:
        # Check if member exists
        cursor.execute("SELECT id FROM members WHERE id = %s", (data['member_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Member not found'}), 404
        
        # Check if trainer exists
        cursor.execute("SELECT id FROM trainers WHERE id = %s", (data['trainer_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Trainer not found'}), 404
        
        query = """
            INSERT INTO assignments (member_id, trainer_id, start_date, end_date, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['member_id'],
            data['trainer_id'],
            data['start_date'],
            data.get('end_date'),
            data.get('notes', '')
        ))
        conn.commit()
        
        # Get the ID of the new assignment
        new_id = cursor.lastrowid
        
        return jsonify({'success': True, 'id': new_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """API to update a trainer assignment"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if assignment exists
        cursor.execute("SELECT id FROM assignments WHERE id = %s", (assignment_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Build update query dynamically based on provided fields
        fields = []
        values = []
        
        update_fields = ['member_id', 'trainer_id', 'start_date', 'end_date', 'notes']
        for field in update_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        query = f"UPDATE assignments SET {', '.join(fields)} WHERE id = %s"
        values.append(assignment_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """API to delete a trainer assignment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if assignment exists
        cursor.execute("SELECT id FROM assignments WHERE id = %s", (assignment_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Delete assignment
        cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
