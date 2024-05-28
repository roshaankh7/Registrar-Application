"The database processing file"
import sqlite3
import contextlib
import sys
#-----------------------------------------------------------------------

_DATABASE_URL = 'file:reg.sqlite?mode=ro'

#-----------------------------------------------------------------------
def customize_input(value):
    "Fixing the input"
    if value:
        new_val = value.replace("_", "@_").replace("%", "@%").lower().replace("\n", "")
        new_val = f"%{new_val}%"
        return new_val
    return value
def get_classes(line):
    "Gets the classes"
    yoo = []
    arr = []
    if line[0] == 'get_overviews':
        prepared = []
        specific_search = []
        criteria = ["dept", "coursenum", "area", "title"]

        for i in criteria:
            if line[1].get(i):
                prepared.append(customize_input(line[1][i]))
                specific_search.append(f"{i} LIKE ? ESCAPE '@'")

        adding_and = " AND ".join(specific_search) if specific_search else "1=1"

        stmt_str = """
        SELECT classid, dept, coursenum, area, title
        FROM classes
        INNER JOIN crosslistings ON classes.courseid = crosslistings.courseid
        INNER JOIN courses ON classes.courseid = courses.courseid
        WHERE {} ORDER BY dept, coursenum, classid""".format(adding_and)

        try:
            with sqlite3.connect(_DATABASE_URL, isolation_level=None, uri=True) as connection:
                cursor = connection.cursor()
                cursor.execute(stmt_str, prepared)
                found_classes = cursor.fetchall()
                if found_classes:
                    yoo.append(True)
                for m in found_classes:
                    yo = {'classid': m[0], 'dept': m[1], 'coursenum': m[2],
                           'area': m[3], 'title': m[4]}
                    arr.append(yo)
                yoo.append(arr)
        except Exception:
            print('Query Error:', file=sys.stderr)
            sys.exit(1)
    return yoo
#-----------------------------------------------------------------------
def getdetails(line):
    "Gets the additional details of the course"
    arr = []
    class_found = None
    try:
        with sqlite3.connect(_DATABASE_URL, isolation_level=None, uri=True) as connection:
            with contextlib.closing(connection.cursor()) as cursor:
                stmt_str = "SELECT classes.courseid, days, starttime, endtime, bldg, "
                stmt_str += "roomnum, dept, coursenum, area, title, descrip, prereqs, profname "
                stmt_str +=  "FROM classes "
                stmt_str +=  "INNER JOIN courses ON classes.courseid = courses.courseid "
                stmt_str +=  "INNER JOIN crosslistings ON classes.courseid "
                stmt_str +=  "= crosslistings.courseid "
                stmt_str +=  "LEFT JOIN coursesprofs ON classes.courseid = coursesprofs.courseid "
                stmt_str +=  "LEFT JOIN profs ON coursesprofs.profid = profs.profid "
                stmt_str +=  "WHERE classid = ? "
                stmt_str +=   "ORDER BY dept, coursenum"
                cursor.execute(stmt_str, [line])
                class_found = cursor.fetchall()
                print(class_found)
                if class_found:
                    m = class_found[0]
                    yo = {'courseid': m[0], 'days': m[1], 'starttime': m[2],
                           'endtime': m[3], 'bldg': m[4],
                              'roomnum': m[5], 'deptcoursenums': [[m[6], m[7]]],
                                'area': m[8], 'title': m[9],
                              'descrip': m[10], 'prereqs': m[11],
                                'profnames': [m[12]]}
                    arr.append(True)
                    arr.append(yo)
    except Exception as ex:
        print(ex, file=sys.stderr)
        return ex, None
    return arr
