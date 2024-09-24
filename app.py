from flask import (Flask, url_for, redirect, request, render_template,
                   jsonify, session, flash)
import sys
import json
import secrets
import bcrypt
import pymysql
import cs304dbi as dbi

DATABASE = 'scottdb'               # global for database to connect to

# based this on https://flask.palletsprojects.com/en/2.3.x/appcontext/#manually-push-a-context
def create_app():
    app = Flask(__name__)
    # we don't really need the app context
    with app.app_context():
        dbi.conf(DATABASE)
    return app
        
app = create_app()
app.secret_key = secrets.token_hex(20)

@app.route('/')
def home():
    return render_template('home.html')
    
@app.route('/list-courses/')
def list_courses():
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    # find courses with at least one student
    curs.execute('''select course from when_to_pair
                    group by course
                    having count(*) > 0''')
    rows = curs.fetchall()
    courses = [ row[0] for row in rows ]
    if len(courses) == 0:
        flash('No courses found')
        return redirect(url_for('home'))
    return render_template('list-courses.html', courses=courses)

@app.route('/get-course/')
def get_course():
    course = request.args['course']
    return redirect(url_for('display_course', course_id=course))

@app.route('/course/<course_id>')
def display_course(course_id):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student_email, student_name from when_to_pair
                    where course = %s
                    order by student_name ASC''',
                 [course_id])
    studs = curs.fetchall()
    if len(studs) == 0:
        flash('No students in that course')
        return redirect(url_for('home'))
    return render_template('select-schedule.html',
                           course_id=course_id,
                           students=studs)

@app.route('/compare/<course_id>')
def compare_two_students(course_id):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student_email, student_name from when_to_pair
                    where course = %s''',
                 [course_id])
    studs = curs.fetchall()
    if len(studs) == 0:
        flash('No students in that course')
        return redirect(url_for('home'))
    return render_template('compare-schedule.html',
                           course_id=course_id,
                           students=studs)


days_of_the_week = 'Sun,Mon,Tue,Wed,Thu,Fri,Sat'.split(',')

@app.route('/save/', methods=["POST"])
def save_schedule():
    print('form is json?', request.is_json)
    if request.is_json:
        print('form json', request.json)
    else:
        print('form data keys', request.form.keys())
        
    course = request.form.get('courseId')
    if not course:
        return jsonify({'error': 'missing key: courseId'})
    email = request.form.get('student')
    if not email:
        return jsonify({'error': 'missing key: student'})
    slots = []
    day_errors = []
    for day in days_of_the_week:
        slot = request.form.get(day)
        if not slot:
            day_errors.append(day)
        else:
            slots.append(slot)
    if len(day_errors) > 0:
        return jsonify({'error': 'missing day keys: '+','.join(day_errors)})
    print('slots', slots)
    slots.append(course)
    slots.append(email)
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    print('slots', slots)
    nrows = curs.execute('''update when_to_pair
                            set Sun = %s, Mon = %s, Tue = %s, Wed = %s, Thu = %s, Fri = %s, Sat = %s
                            where course = %s and student_email = %s''',
                         slots)
    conn.commit()
    if nrows == 0:
        return jsonify({'error': 'zero rows updated; wrong course or email?'})
    else:
        return jsonify({'error': False})

@app.route('/get-schedule/')
def get_schedule():
    email = request.args.get('student')
    course = request.args.get('courseId')
    if email is None or email == '':
        return jsonify({'error': 'no email'})
    if course is None or course == '':
        return jsonify({'error': 'no courseId'})
    print('args', [course, email])
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    # have to add zero to get the numeric value. tedious, but okay
    nrows = curs.execute('''select course, student_email, student_name,
                                   sun+0, mon+0, tue+0, wed+0, thu+0, fri+0, sat+0
                            from when_to_pair
                            where course = %s and student_email = %s''',
                         [course, email])
    if nrows == 0:
        return jsonify({'error': 'no schedule found; wrong course or email?'})
    else:
        row = curs.fetchone()
        print('row', row)
        return jsonify({'error': False, 'row': row})
    

# See https://stackoverflow.com/questions/25860304/how-do-i-set-response-headers-in-flask
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
    
@app.route('/info/')
def info():
    return f'<h2>Python Path</h2><p>{sys.path}</p>'

if __name__ == '__main__':
    import sys,os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)
