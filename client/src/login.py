# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(560, 503)
        Dialog.setMinimumSize(QtCore.QSize(560, 503))
        Dialog.setMaximumSize(QtCore.QSize(560, 503))
        self.connect_button = QtWidgets.QPushButton(Dialog)
        self.connect_button.setGeometry(QtCore.QRect(100, 430, 141, 31))
        self.connect_button.setObjectName("connect_button")
        self.IP_edit = QtWidgets.QLineEdit(Dialog)
        self.IP_edit.setGeometry(QtCore.QRect(50, 70, 461, 41))
        self.IP_edit.setObjectName("IP_edit")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(50, 40, 141, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(50, 130, 181, 16))
        self.label_2.setObjectName("label_2")
        self.port_edit = QtWidgets.QLineEdit(Dialog)
        self.port_edit.setGeometry(QtCore.QRect(50, 160, 461, 41))
        self.port_edit.setObjectName("port_edit")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(50, 220, 141, 16))
        self.label_3.setObjectName("label_3")
        self.username_edit = QtWidgets.QLineEdit(Dialog)
        self.username_edit.setGeometry(QtCore.QRect(50, 250, 461, 41))
        self.username_edit.setObjectName("username_edit")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setGeometry(QtCore.QRect(50, 310, 121, 16))
        self.label_4.setObjectName("label_4")
        self.password_edit = QtWidgets.QLineEdit(Dialog)
        self.password_edit.setGeometry(QtCore.QRect(50, 340, 461, 41))
        self.password_edit.setObjectName("password_edit")
        self.login_button = QtWidgets.QPushButton(Dialog)
        self.login_button.setGeometry(QtCore.QRect(320, 430, 141, 31))
        self.login_button.setObjectName("login_button")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.connect_button.setText(_translate("Dialog", "Connect"))
        self.label.setText(_translate("Dialog", "IP："))
        self.label_2.setText(_translate("Dialog", "Port:"))
        self.label_3.setText(_translate("Dialog", "Username:"))
        self.label_4.setText(_translate("Dialog", "Password:"))
        self.login_button.setText(_translate("Dialog", "Login"))
