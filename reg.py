"The reg.py program GUI"
import argparse
import socket
import pickle
import queue
import threading
from PyQt5 import QtWidgets, QtCore, QtGui

#-----------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    "Creating the GUI"
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.event_queue = queue.Queue()
        self.current_worker_thread = None
        self.debounce_timer = None
        self.resize(1000,600)
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.label = QtWidgets.QLabel('Dept: ', self.main_widget)
        self.line_edit = QtWidgets.QLineEdit('', self.main_widget)
        self.grid_layout = QtWidgets.QGridLayout(self.main_widget)
        self.grid_layout.addWidget(self.label, 0, 0,1,1 )
        self.grid_layout.addWidget(self.line_edit, 0, 1,1,1 )
        self.setWindowTitle("Princeton University Class Search")
        self.label = QtWidgets.QLabel('Number: ', self.main_widget)
        self.line_edit_2 = QtWidgets.QLineEdit('', self.main_widget)
        self.grid_layout.addWidget(self.label, 1, 0,1,1 )
        self.grid_layout.addWidget(self.line_edit_2, 1, 1,1,1 )
        self.label = QtWidgets.QLabel('Area: ', self.main_widget)
        self.line_edit_3 = QtWidgets.QLineEdit('', self.main_widget)
        self.grid_layout.addWidget(self.label, 2, 0,1,1 )
        self.grid_layout.addWidget(self.line_edit_3, 2, 1,1,1 )
        self.label = QtWidgets.QLabel('Title: ', self.main_widget)
        self.line_edit_4 = QtWidgets.QLineEdit('', self.main_widget)
        self.grid_layout.addWidget(self.label, 3, 0,1,1 )
        self.grid_layout.addWidget(self.line_edit_4, 3, 1,1,1 )
        self.listwidget =QtWidgets.QListWidget()
        self.grid_layout.addWidget(self.listwidget, 4, 0,1,3 )
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop)
        self.line_edit.textChanged.connect(self.submit)
        self.line_edit_2.textChanged.connect(self.submit)
        self.line_edit_3.textChanged.connect(self.submit)
        self.line_edit_4.textChanged.connect(self.submit)
        font = QtGui.QFont("Courier New", 10)
        self.listwidget.setFont(font)
        self.listwidget.itemClicked.connect(self.getmore_details)
        self.listwidget.itemActivated.connect(self.getmore_details)
        self.event_queue_timer = QtCore.QTimer(self)
        self.event_queue_timer.timeout.connect(self.poll_event_queue_helper)
        self.event_queue_timer.setInterval(100)
        self.event_queue_timer.start()
    def poll_event_queue_helper(self):
        "The poll event queue helper"
        while not self.event_queue.empty():
            success, data = self.event_queue.get()
            if success:
                self.listwidget.clear()
                for k in data[1]:
                    self.listwidget.addItem(str(k["classid"])
                        + "   "+ str(k["dept"]) +
                        "   " +str(k["coursenum"]) + "   " + 
                        str(k["area"]) + "   " + str(k["title"]))
                if self.listwidget.count() > 0:
                    self.listwidget.setCurrentRow(0)
            else:
                print("Error retrieving data:", data)
#-------------------------------------------------------------------
    def debounced_submit(self):
        "The debounced getting classes"
        if self.debounce_timer is not None:
            self.debounce_timer.cancel()
        self.debounce_timer = threading.Timer(0.5, self.submit)
        self.debounce_timer.start()
#----------------------------------------------------------------
    def submit(self):
        "Getting the classees"
        if self.current_worker_thread and self.current_worker_thread.is_alive():
            self.current_worker_thread.stop()
        dept_input = self.line_edit.text().strip()
        number_input = self.line_edit_2.text().strip()
        area_input = self.line_edit_3.text().strip()
        title_input = self.line_edit_4.text().strip()
        sending_data = ['get_overviews', {'dept': dept_input,
                    'coursenum': number_input, 'area': 
                    area_input, 'title': title_input}]
        self.current_worker_thread = WorkerThread(self.host,
                                                   self.port, sending_data, self.event_queue)
        self.current_worker_thread.start()
#-------------------------------------------------------------------
    def getmore_details(self, item):
        "To get more class details"
        try:
            get_num = item.text().strip()
            res = [int(i) for i in get_num.split() if i.isdigit()]
            send_data = ['get_detail', res[0]]
            with socket.socket() as sock:
                sock.connect((self.host, self.port))
                floo = sock.makefile(mode='wb')
                pickle.dump(send_data, floo)
                floo.flush()
                flo = sock.makefile(mode='rb')
                detailz = pickle.load(flo)
                m = detailz[1]
                details_text = f"""Course ID: {m["courseid"]} \n
Days: {m["days"]}
Start Time: {m["starttime"]}
End Time: {m["endtime"]}
Building: {m["bldg"]}
Room: {m["roomnum"]} \n
Dept and Number: {m["deptcoursenums"][0][0]} {m["deptcoursenums"][0][1]} \n
Area: {m["area"]} \n
Title: {m["title"]} \n
Description: {m["descrip"]} \n
Prerequisites: {m["prereqs"]} \n
Professor: {', '.join(m["profnames"])}"""
                message_box = QtWidgets.QMessageBox(self)
                message_box.setWindowTitle("Class Details")
                message_box.setText(details_text)
                message_box.exec_()

        except Exception as e:
            print(f"Error in getting details: {e}")
#----------------------------------------------------------------------
class WorkerThread (threading.Thread):
    "The worker thread"
    def __init__(self, host, port,data, event_queue):
        threading.Thread.__init__(self)
        self._host = host
        self._port = port
        self.data = data
        self._event_queue = event_queue
        self._should_stop = False
    def stop(self):
        "To stop" 
        self._should_stop = True
    def run(self):
        try:
            if self._should_stop:
                return
            with socket.socket() as sock:
                sock.connect((self._host, self._port))
                floo = sock.makefile(mode='wb')
                if self._should_stop:
                    return
                pickle.dump(self.data, floo)
                floo.flush()
                flo = floo = sock.makefile(mode='rb')
                if self._should_stop:
                    return
                courses = pickle.load(flo)
            if not self._should_stop:
                self._event_queue.put((True, courses))
        except Exception as ex:
            if not self._should_stop:
                self._event_queue.put((False, str(ex)))
#--------------------------------------------------------------------
def main():
    "The main"
    app = QtWidgets.QApplication([])
    parser = argparse.ArgumentParser(allow_abbrev=False,description
    = "Client for the registrar application")
    parser.add_argument('host',type=str, metavar='host',
        help=" the host on which the server is running")
    parser.add_argument('port',type=int, metavar='port',
        help="  the port at which the server is listening")
    args = parser.parse_args()
    interface = MainWindow(args.host, args.port)
    interface.show()
    app.setApplicationDisplayName('Class Details')
    app.exec_()

if __name__ == '__main__':
    main()
