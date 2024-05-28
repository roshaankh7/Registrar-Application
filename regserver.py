import argparse
import sqlite3
import socket
import sys
import pickle
import contextlib
import threading
import time
import database

def get_classes(sock):
    """ Retrieve class information based on requests. """
    database_url = 'file:reg.sqlite?mode=ro'
    request = pickle.load(sock.makefile(mode='rb'))
    if request[0] == 'get_overviews':
        courses = database.get_classes(request)
        output = sock.makefile('wb')
        pickle.dump(courses, output)
        output.flush()
    else:
        response = []
        class_found = None
        try:
            with sqlite3.connect(database_url, isolation_level=None, uri=True) as connection:
                with contextlib.closing(connection.cursor()) as cursor:
                    query = """
                        SELECT classes.courseid, days, starttime, endtime, bldg, roomnum, dept, coursenum,
                               area, title, descrip, prereqs, profname
                        FROM classes
                        INNER JOIN courses ON classes.courseid = courses.courseid
                        INNER JOIN crosslistings ON classes.courseid = crosslistings.courseid
                        LEFT JOIN coursesprofs ON classes.courseid = coursesprofs.courseid
                        LEFT JOIN profs ON coursesprofs.profid = profs.profid
                        WHERE classid = ?
                        ORDER BY dept, coursenum
                    """
                    cursor.execute(query, [request[1]])
                    class_found = cursor.fetchall()
                    if class_found:
                        data = class_found[0]
                        class_info = {
                            'courseid': data[0], 'days': data[1], 'starttime': data[2],
                            'endtime': data[3], 'bldg': data[4], 'roomnum': data[5], 
                            'deptcoursenums': [[data[6], data[7]]], 'area': data[8], 
                            'title': data[9], 'descrip': data[10], 'prereqs': data[11], 'profnames': [data[12]]
                        }
                        response.extend([True, class_info])
                        output = sock.makefile('wb')
                        pickle.dump(response, output)
                        output.flush()

        except sqlite3.DataError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

        if not class_found:
            print('Class Not Available', file=sys.stderr)
            response.extend([False, "Class Not Found"])
            sys.exit(1)

class ClientHandlerThread(threading.Thread):
    """ Thread to handle client requests. """
    def __init__(self, sock, delay):
        super().__init__()
        self.sock = sock
        self.delay = delay

    def run(self):
        print('Spawned child thread')
        time.sleep(self.delay)
        get_classes(self.sock)

def main():
    """ Main function to start the server. """
    parser = argparse.ArgumentParser(allow_abbrev=False,
                                     description="Server for the registrar application")
    parser.add_argument('port', type=int, help="Port number where the server listens")
    parser.add_argument('delay', type=int, help="Initial delay before processing requests")
    args = parser.parse_args()

    try:
        server_sock = socket.socket()
        server_sock.bind(('', args.port))
        server_sock.listen()
        print('Listening')

        while True:
            try:
                client_sock, client_addr = server_sock.accept()
                print('Accepted connection')
                thread = ClientHandlerThread(client_sock, args.delay)
                thread.start()
            except Exception:
                print('Connection Error', file=sys.stderr)

    except Exception as ex:
        print(ex, file=sys.stderr)

if __name__ == '__main__':
    main()
