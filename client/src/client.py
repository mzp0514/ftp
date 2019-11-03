

import sys
import socket
import os
import random
import re
import time
import threading
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal

from main import Ui_Dialog as main_dialog
from login import Ui_Dialog as login_dialog


class Client:
    def __init__(self):
        pass
    
    
    def connect(self, server_ip, server_port):
        self.localIP = "127.0.0.1"
        self.dt_skt = None
        self.dt_skt2 = None
        self.have_recv = 0
        self.is_tranferring = 0
        self.transfer_unfinished = 0
        self.progress = 0
        self.cur_file_dir = ""
        self.cmd_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.cmd_skt.connect((server_ip, server_port))
            buf = self.cmd_skt.recv(8192).decode()[:-1]
            print(buf)
        except ConnectionError:
            print("Connection Error")
            return -1
        else:
            return 0


    def send_file(self, dir):
        f_name = dir.split("/")[-1]
        f = open(dir, 'rb')
        if self.is_pasv:
            j = 0
            #file_buf = self.dt_skt.sendall(f.read())
            while self.have_sent < self.total:
                time.sleep(0.00001)
                j += 1
                self.have_sent += self.dt_skt.send(f.read(8192))
                self.progress = self.have_sent/self.total
                if j % 10 == 0 or self.progress == 1:
                    md.update_uploading()

            self.dt_skt.close()
            self.dt_skt = None

        else:
            j = 0
            s, _ = self.dt_skt.accept()

            while self.have_sent < self.total:
                time.sleep(0.00001)
                j += 1
                self.have_sent += s.send(f.read(8192))
                self.progress = self.have_sent/self.total
                if j % 10 == 0 or self.progress == 1:
                    md.update_uploading()

            s.close()
        
        if self.have_sent == self.total:
            buf = self.cmd_skt.recv(8192).decode()[:-1]
            print(buf)
            md.up_finish.emit(f_name)
            

        self.is_tranferring = 0
        f.close()
        


    def recv_file(self, dir):
        f_name = dir.split("/")[-1]

        print(f_name, self.have_recv)
        
        f = open(dir, 'wb')
        
        f.seek(self.have_recv, 0)

        if self.is_pasv:
            j = 0
            while(1):
                j += 1
                if self.dt_skt:
                    file_buf = self.dt_skt.recv(8192)
                else:
                    break

                if not file_buf:
                    break

                f.write(file_buf)
                self.have_recv += len(file_buf)
                self.progress = self.have_recv/self.total
                if j % 10 == 0 or self.progress == 1:
                    md.update_downloading()

            if self.dt_skt:
                self.dt_skt.close()
                self.dt_skt = None

        else:
            j = 0
            self.dt_skt2, _ = self.dt_skt.accept()
            while(1):
                j += 1
                if self.dt_skt2:
                    file_buf = self.dt_skt2.recv(8192)
                else:
                    break

                if not file_buf:
                    break
                f.write(file_buf)

                self.have_recv += len(file_buf)
                self.progress = self.have_recv/self.total
                if j % 10 == 0 or self.progress == 1:
                    md.update_downloading()

            if self.dt_skt2:
                self.dt_skt2.close()
        
        f.close()
        self.is_tranferring = 0

        if self.progress == 1:
            self.have_recv = 0
            self.transfer_unfinished = 0
            md.down_finish.emit(f_name, dir)
            buf = self.cmd_skt.recv(512).decode()[:-1]
            print(buf)
                

    def execute(self, command, dir = ""):

        command = command.strip()
        cmd =  command.split(' ')[0]

        if self.is_tranferring and cmd != "REST":
            print("transferring")
            return "File transferring."


        if cmd in ["USER", "PASS", "SYST", "TYPE", "MKD", "CWD", "PWD", "RMD", "RNFR", "RNTO"]:
            self.cmd_skt.send((command + "\r\n").encode())
            buf = self.cmd_skt.recv(512).decode()[:-1]
            print(buf)
            return buf

        elif cmd == "QUIT" or cmd == "ABOR":
            self.cmd_skt.send((command + "\r\n").encode())
            buf = self.cmd_skt.recv(512).decode()[:-1]
            print(buf)
            self.cmd_skt.close()
            if self.dt_skt is not None:
                self.dt_skt.close()
            return 0

        elif cmd == "PORT":
            if self.dt_skt is not None:
                self.dt_skt.close()
                self.dt_skt = None
            self.is_pasv = 0
            
            while(1):
                self.data_port = random.randint(20000, 65535)
                try:
                    self.dt_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.dt_skt.bind((self.localIP,self.data_port))
                    self.dt_skt.listen()
                except:
                    continue
                else:
                    break

            cmd_str = "PORT %s,%d,%d\r\n" % (self.localIP.replace(".", ","), self.data_port // 256, self.data_port % 256)
            self.cmd_skt.send(cmd_str.encode())
            buf = self.cmd_skt.recv(512).decode()[:-1]
            print(buf)
            if not buf.startswith("200"):
                self.dt_skt.close()
                self.dt_skt = None

        elif cmd == "PASV":

            if self.dt_skt is not None:
                self.dt_skt.close()
            self.is_pasv = 1
            self.cmd_skt.send("PASV" + "\r\n".encode())
            buf = self.cmd_skt.recv(512).decode()[:-1]
            print(buf)

            if buf.startswith("227"):
                pasv_addr = re.split('[()]',buf)[1]
                pasv_addr = pasv_addr.split(',')
                self.data_port = int(pasv_addr[-1]) + 256 * int(pasv_addr[-2])
                self.pasv_ip = pasv_addr[0] + '.' + pasv_addr[1] + '.' + pasv_addr[2] + '.' + pasv_addr[3]
                self.dt_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.dt_skt.connect((self.pasv_ip, self.data_port))
        
        elif cmd == "REST":
            if self.is_pasv:
                self.dt_skt.close()
                self.dt_skt = None
            else:
                self.dt_skt2.close()
                self.dt_skt2 = None

            time.sleep(1)

            self.cmd_skt.send(("REST " + str(self.have_recv) + "\r\n").encode())
            buf = self.cmd_skt.recv(512).decode()
            print(buf)


        elif cmd == "RETR":
            self.cmd_skt.send((command + "\r\n").encode())
            buf = self.cmd_skt.recv(512).decode()
            
            if buf.startswith("150"):
                self.is_tranferring = 1
                self.transfer_unfinished = 1
                self.total = int(buf[buf.rfind("(") + 1 : buf.rfind("bytes)")])
                self.progress = self.have_recv/self.total
                f_name = command.split(" ")[-1]
                
                md.show_downloading(f_name)
                
                if dir == "":
                    dir = self.cur_file_dir
                else:
                    self.cur_file_dir = dir

                print(dir)

                t = threading.Thread(target=self.recv_file, args=(dir,))
                t.setDaemon(True)
                t.start()
            

        elif cmd == "STOR":

            self.cmd_skt.send((command + "\r\n").encode())
            buf = self.cmd_skt.recv(512).decode()[:-1]
            print(buf)

            if buf.startswith("150"):
                self.is_tranferring = 1
                self.have_sent = 0
                self.progress = self.have_sent/self.total

                f_name = command.split(" ")[-1]
                md.show_uploading(f_name)


                t2 = threading.Thread(target=self.send_file, args=(dir,))
                t2.setDaemon(True)
                t2.start()


        elif cmd == "LIST":

            self.cmd_skt.send((command + "\r\n").encode())
            buf = self.cmd_skt.recv(8192).decode()[:-1]
            print(buf)

            if buf.startswith("150"):
                f_info = ""
                if self.is_pasv:

                    while(1):
                        file_buf = self.dt_skt.recv(8192)
                        if not file_buf:
                            break
                        f_info += file_buf.decode()

                    self.dt_skt.close()
                    self.dt_skt = None

                else:

                    s, _ = self.dt_skt.accept()

                    while(1):
                        file_buf = s.recv(8192)
                        if not file_buf:
                            break
                        f_info += file_buf.decode()

                    s.close()
                
                buf = self.cmd_skt.recv(512).decode()[:-1]
                print(buf)
                return f_info



class MainDialog(QtWidgets.QDialog, main_dialog):

    down_finish = pyqtSignal([str, str])
    up_finish = pyqtSignal([str])
    
    def __init__(self):
        super(MainDialog, self).__init__()
        self.setupUi(self)

        self.upload_button.setIcon(QtGui.QIcon("icons/upload.png"))
        self.upload_button.setIconSize(QtCore.QSize(30, 30))
        self.upload_button.clicked.connect(self.upload)

        self.download_button.setIcon(QtGui.QIcon("icons/download.png"))
        self.download_button.setIconSize(QtCore.QSize(30, 30))
        self.download_button.clicked.connect(self.download)

        self.goto_button.setIcon(QtGui.QIcon("icons/next.png"))
        self.goto_button.setIconSize(QtCore.QSize(30, 30))

        self.back_button.setIcon(QtGui.QIcon("icons/back.png"))
        self.back_button.setIconSize(QtCore.QSize(30, 30))

        self.home_button.setIcon(QtGui.QIcon("icons/home.png"))
        self.home_button.setIconSize(QtCore.QSize(30, 30))

        self.mkdir_button.setIcon(QtGui.QIcon("icons/folder.png"))
        self.mkdir_button.setIconSize(QtCore.QSize(30, 30))

        self.disconnect_button.clicked.connect(self.quit)

        self.files.setColumnCount(4)
        self.files.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.files.setHorizontalHeaderLabels(("Property", "Name", "Size", "Last Modification"))
        self.files.setSelectionBehavior(QTableWidget.SelectRows)
        self.files.verticalHeader().setVisible(False)
        self.files.setShowGrid(False)
        self.files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files.customContextMenuRequested.connect(self.gen_menu)
        self.files.itemDoubleClicked.connect(lambda item: self.goto2(item.row()))

        self.uploading_files.setColumnCount(2)
        self.uploading_files.horizontalHeader().setStretchLastSection(True)
        self.uploading_files.setHorizontalHeaderLabels(("Filename", "Progress"))
        self.uploading_files.setSelectionBehavior(QTableWidget.SelectRows)
        self.uploading_files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.uploading_files.verticalHeader().setVisible(False)
        self.uploading_files.setShowGrid(False)

        self.downloading_files.setColumnCount(2)
        self.transferred_files.horizontalHeader().resizeSection(0, 100)
        self.downloading_files.horizontalHeader().setStretchLastSection(True)
        self.downloading_files.setHorizontalHeaderLabels(("Filename", "Progress"))
        self.downloading_files.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloading_files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.downloading_files.verticalHeader().setVisible(False)
        self.downloading_files.setShowGrid(False)
        
        self.transferred_files.setColumnCount(4)
        self.transferred_files.horizontalHeader().resizeSection(0, 100)
        self.transferred_files.horizontalHeader().resizeSection(1, 100)
        self.transferred_files.horizontalHeader().resizeSection(2, 100)
        self.transferred_files.horizontalHeader().setStretchLastSection(True)
        self.transferred_files.setHorizontalHeaderLabels(("Filename", "D/U", "Progress", "Location"))
        self.transferred_files.setSelectionBehavior(QTableWidget.SelectRows)
        self.transferred_files.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.transferred_files.verticalHeader().setVisible(False)
        self.transferred_files.setShowGrid(False)
        self.transferred_files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.transferred_files.customContextMenuRequested.connect(self.gen_menu2)

        self.downloading_bar.setValue(0)
        self.uploading_bar.setValue(0)

        self.lineEdit.setText(self.get_dir())
        self.show_files()

        self.back_button.clicked.connect(self.back)
        self.home_button.clicked.connect(self.home)
        self.goto_button.clicked.connect(self.goto)
        self.mkdir_button.clicked.connect(self.mkdir)

        self.pause_button.clicked.connect(self.download_pause)
        self.pause_button.setEnabled(False)
        self.continue_button.clicked.connect(self.download_continue)
        self.continue_button.setEnabled(False)

        self.down_finish.connect(self.download_finished)
        self.up_finish.connect(self.upload_finished)

        self.cur_dir = ""

        
    def download_finished(self, f_name, f_path):
        # self.downloading_bar.setValue(0)
        self.pause_button.setEnabled(False)
        num = self.transferred_files.rowCount()
        self.transferred_files.setRowCount(num + 1)
        self.transferred_files.setItem(num, 0, QTableWidgetItem(f_name))
        self.transferred_files.setItem(num, 1, QTableWidgetItem("Download"))
        self.transferred_files.setItem(num, 3, QTableWidgetItem("local:"+f_path))
        pro_bar = QProgressBar()
        pro_bar.setValue(100)
        self.transferred_files.setCellWidget(num, 2, pro_bar)


    def upload_finished(self, f_name):
        # self.uploading_bar.setValue(0)
        self.show_files()
        num = self.transferred_files.rowCount()
        self.transferred_files.setRowCount(num + 1)
        self.transferred_files.setItem(num, 0, QTableWidgetItem(f_name))
        self.transferred_files.setItem(num, 1, QTableWidgetItem("Upload"))
        self.transferred_files.setItem(num, 3, QTableWidgetItem("remote:"+self.cur_dir))
        pro_bar = QProgressBar()
        pro_bar.setValue(100)
        self.transferred_files.setCellWidget(num, 2, pro_bar)


    def quit(self):
        global client
        recv = client.execute("QUIT")
        if recv == "File transferring.":
            QMessageBox.information(self, "Sorry", recv, QMessageBox.Ok)
            return
        self.destroy()
        sys.exit(app.exec_())


    def closeEvent(self, event):
        self.quit()


    def get_dir(self):
        global client
        recv = client.execute("PWD")
        if recv == "File transferring.":
            QMessageBox.information(self, "Sorry", recv, QMessageBox.Ok)
            return
        recv = recv.split("\"")[1]
        return recv

    
    def back(self):
        global client
        recv = client.execute("CWD ..")
        if recv == "File transferring.":
            QMessageBox.information(self, "Sorry", recv, QMessageBox.Ok)
            return
        self.lineEdit.setText(self.get_dir())
        self.show_files()


    def home(self):
        global client
        recv = client.execute("CWD /")
        if recv == "File transferring.":
            QMessageBox.information(self, "Sorry", recv, QMessageBox.Ok)
            return
        self.lineEdit.setText(self.get_dir())
        self.show_files()


    def goto(self):
        global client
        recv = client.execute("CWD " + self.lineEdit.text())
        if recv == "File transferring.":
            QMessageBox.information(self, "Sorry", recv, QMessageBox.Ok)
            return
        self.lineEdit.setText(self.get_dir())
        if recv.startswith("550"):
            return 
        self.show_files()


    def goto2(self, row):
        f_name = self.files.item(row, 1).text()
        path = self.get_dir() + '/' + f_name
        if self.files.item(row, 0).text()[0] != 'd':
            return
        else:
            global client
            recv = client.execute("CWD " + path)
            if recv == "File transferring.":
                QMessageBox.information(self, "Sorry", recv, QMessageBox.Ok)
                return
            
            if recv.startswith("550"):
                return 
            self.lineEdit.setText(path)
            self.show_files()


    def show_files(self):
        global client
        recv = client.execute("PORT")
        recv = client.execute("LIST")

        file_rows = re.split(r"\r\n|\n", recv)

        self.files.setRowCount(len(file_rows)-1)
        for i in range(len(file_rows) - 1):
            s = re.split(r"\s+", file_rows[i])
            items = [QTableWidgetItem(s[0]), 
                    QTableWidgetItem(" ".join(s[8:])),
                    QTableWidgetItem(s[4]), 
                    QTableWidgetItem(s[5]+" "+s[6]+" "+s[7])]
            for j in range(4):
                self.files.setItem(i, j, items[j])


    def show_downloading(self, f_name):
        self.downloading_name.setText(f_name)  


    def show_uploading(self, f_name):
        self.uploading_name.setText(f_name)

        
    def update_downloading(self):
        self.downloading_bar.setValue(client.progress * 100)

        
    def update_uploading(self):
        self.uploading_bar.setValue(client.progress * 100)

    
    def mkdir(self):
        if client.is_tranferring:
            QMessageBox.information(self, "Sorry", "File transferring.", QMessageBox.Ok)
            return

        foldername, _ = QInputDialog.getText(self, "New folder", "folder name", QLineEdit.Normal, "")
        recv = client.execute("MKD " + foldername)
        
        print(recv)
        self.show_files()


    def rmdir(self):
        if client.is_tranferring:
            QMessageBox.information(self, "Sorry", "File transferring.", QMessageBox.Ok)
            return
        
        row_num = -1
        for i in self.files.selectionModel().selection().indexes():
            row_num = i.row()
            
        recv = client.execute("RMD " + self.files.item(row_num, 1).text())
        
        print(recv)
        self.show_files()


    def rename(self):
        if client.is_tranferring:
            QMessageBox.information(self, "Sorry", "File transferring.", QMessageBox.Ok)
            return
        
        row_num = -1
        for i in self.files.selectionModel().selection().indexes():
            row_num = i.row()

        newname, _ = QInputDialog.getText(self, "Rename", "new name", QLineEdit.Normal, "")
        recv = client.execute("RNFR " + self.files.item(row_num, 1).text())
        print(recv)
        recv = client.execute("RNTO " + newname)
        print(recv)
        self.show_files()


    def gen_menu(self, pos):
        global client
        row_num = -1
        for i in self.files.selectionModel().selection().indexes():
            row_num = i.row()

        menu = QMenu()
        item1 = menu.addAction(u"New folder")
        item2 = menu.addAction(u"Rename")
        item3 = menu.addAction(u"Remove")

        action = menu.exec_(self.files.mapToGlobal(pos))
        if action == item1:
            self.mkdir()
            
        elif action == item2:
            self.rename()

        elif action == item3:
            self.rmdir()


    def gen_menu2(self, pos):
        global client
        row_num = -1
        for i in self.transferred_files.selectionModel().selection().indexes():
            row_num = i.row()

        menu = QMenu()
        item1 = menu.addAction(u"Delete Record")

        action = menu.exec_(self.transferred_files.mapToGlobal(pos))
        if action == item1:
            self.transferred_files.removeRow(row_num)

            
    def download_pause(self):

        self.continue_button.setEnabled(True)
        self.pause_button.setEnabled(False)

        client.execute("REST")
        

    def download_continue(self):

        self.continue_button.setEnabled(False)
        self.pause_button.setEnabled(True)

        client.execute("PORT")
        client.execute("RETR " + self.downloading_name.text())
        
        
    def download(self):

        if client.is_tranferring:
            QMessageBox.information(self, "Sorry", "File transferring.", QMessageBox.Ok)
            return

        if client.transfer_unfinished:
            QMessageBox.information(self, "Sorry", "File transfer unfinished.", QMessageBox.Ok)
            return 
        
        row_num = -1
        for i in self.files.selectionModel().selection().indexes():
            row_num = i.row()

        if row_num == -1:
            return

        f_name = self.files.item(row_num, 1).text()

        if self.files.item(row_num, 0).text()[0] == 'd':
            return

        path = QFileDialog.getExistingDirectory(self, os.getcwd())

        if path == "":
            return

        try:
            f = open(path + "/" + f_name, "wb")
        except:
            QMessageBox.information(self, "Open", "write file error", QMessageBox.Ok)
            return
        else:
            f.close()
        
        recv = client.execute("PORT")

        self.pause_button.setEnabled(True)
        client.execute("RETR " + f_name, path + "/" + f_name)
        

    def upload(self):
        global client

        if client.is_tranferring:
            QMessageBox.information(self, "Sorry", "File transferring.", QMessageBox.Ok)
            return

        f_path = QFileDialog.getOpenFileName(self, "Open", os.getcwd())[0]

        if f_path == "":
            return

        try:
            f = open(f_path, "rb")
        except:
            QMessageBox.information(self, "Open", "read file error", QMessageBox.Ok)
            return
        else:
            f.close()

        recv = client.execute("PORT")
            
        client.total = os.path.getsize(f_path)
        print("total:", client.total)
        f_name = f_path.split('/')[-1]

        self.cur_dir = self.get_dir()

        client.execute("STOR " + f_name, f_path)


class LoginDialog(QtWidgets.QDialog, login_dialog):
    def __init__(self):
        super(LoginDialog, self).__init__()
        self.setupUi(self)
        self.has_cnted = 0
        
        self.username_edit.setEnabled(False)
        self.password_edit.setEnabled(False)
        self.login_button.setEnabled(False)
        self.connect_button.clicked.connect(self.connect)
        self.login_button.clicked.connect(self.login)

    def closeEvent(self, event):

        if self.has_cnted:
            client.execute("QUIT")

        sys.exit(app.exec_())


    def connect(self):

        global client
        ip = self.IP_edit.text()
        port = self.port_edit.text()

        if ip == "":
            ip = "127.0.0.1"

        if port == "":
            port = 21

        if client.connect(ip, int(port)) == 0:
            self.username_edit.setEnabled(True)
            self.password_edit.setEnabled(True)
            self.login_button.setEnabled(True)
            self.has_cnted = 1
        else:
            QMessageBox.information(self, "Connection", "Connection error", QMessageBox.Ok)


    
    def login(self):
        global client
        username = self.username_edit.text()
        password = self.password_edit.text()

        if username == "" and password == "":
            username = "anonymous"
            password = ""

        recv = client.execute("USER " + username)
        print(recv)
        if recv.startswith("331"):
            recv = client.execute("PASS " + password)
            print(recv)
            if recv.startswith("230"):
                createMainDialog()
                self.destroy()
            else:
                QMessageBox.information(self, "Login", "Login error", QMessageBox.Ok)



def createMainDialog():
    global md
    md = MainDialog()
    md.show()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    client = Client()
    
    ld = LoginDialog()
    ld.show()


    sys.exit(app.exec_())