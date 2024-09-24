import sys
import csv
import cs304dbi as dbi

def insert_students(conn, course, csv_file):
    '''CSV file is assumed to have two columns: student_name and
    student_email. Also assumed to have a first line of headers.'''
    curs = dbi.cursor(conn)
    with open(csv_file, 'r') as fin:
        reader = csv.reader(fin)
        next(reader)
        for name,email in reader:
            curs.execute('''insert into scottdb.when_to_pair
                            values(%s, %s, %s, 0, 0, 0, 0, 0, 0, 0)''',
                         [course, email, name])
    conn.commit()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('''Usage: script course csv_file''')
        sys.exit()
    dbi.conf('scottdb')
    conn = dbi.connect()
    insert_students(conn, sys.argv[1], sys.argv[2])
