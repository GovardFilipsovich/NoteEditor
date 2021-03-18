import sys
import os
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QPlainTextEdit, QRadioButton, QCheckBox, QLabel, \
    QFileDialog
from PyQt5 import QtCore, QtGui, QtWidgets
from pydub import AudioSegment
from copy import copy
from pydub.playback import play
import simpleaudio as sa
import sqlite3
import pickle


class Note:
    def __init__(self, duration, ton, sound):
        self.ton = ton
        self.duration = duration
        self.start_sound = sound
        sound = AudioSegment.from_wav(sound)
        dur = sound.duration_seconds
        # Нота обрезается соответственно коэффициенту duration
        self.sound = sound[:dur * duration * 1000]
        self.x = 0
        self.y = 0
        # Форма нужна для восстановления вида нот из объекта мелодии. Служит номером картинки в списке,
        # который определен в главном классе
        self.form = 0

    def change_ton(self, chg_ton):
        # Здесь уменьшается или увеличивается количество фреймов, а частота фреймов устонавливается такая
        # же как на оригинальной ноте, что позволяет сменить ей тон.
        sound = self.sound._spawn(self.sound.raw_data, overrides={
            "frame_rate": int(self.sound.frame_rate * chg_ton)
        }).set_frame_rate(self.sound.frame_rate)
        dur = self.sound.duration_seconds * 1000
        # После этого обрезается длительность, чтобы нота звучала столько же, сколько оригинальная
        sound = sound[:dur]
        snd = Note(self.duration, self.ton, self.start_sound)
        snd.sound = sound
        return snd


# Оперделение нот нужно для того, чтобы потом было легче работать с их объединением
# Определение целых нот
c = Note(1, "c", "Ноты/c0.wav")
d = Note(1, "d", "Ноты/d0.wav")
e = Note(1, "e", "Ноты/e0.wav")
f = Note(1, "f", "Ноты/f0.wav")
g = Note(1, "g", "Ноты/g0.wav")
a = Note(1, "a", "Ноты/a0.wav")
h = Note(1, "h", "Ноты/h0.wav")
# Определение половин
c_2 = Note(0.5, "c", "Ноты/c0.wav")
d_2 = Note(0.5, "d", "Ноты/d0.wav")
e_2 = Note(0.5, "e", "Ноты/e0.wav")
f_2 = Note(0.5, "f", "Ноты/f0.wav")
g_2 = Note(0.5, "g", "Ноты/g0.wav")
a_2 = Note(0.5, "a", "Ноты/a0.wav")
h_2 = Note(0.5, "h", "Ноты/h0.wav")
# Определение четвертей
c_4 = Note(0.25, "c", "Ноты/c0.wav")
d_4 = Note(0.25, "d", "Ноты/d0.wav")
e_4 = Note(0.25, "e", "Ноты/e0.wav")
f_4 = Note(0.25, "f", "Ноты/f0.wav")
g_4 = Note(0.25, "g", "Ноты/g0.wav")
a_4 = Note(0.25, "a", "Ноты/a0.wav")
h_4 = Note(0.25, "h", "Ноты/h0.wav")
# Определение восьмых
c_8 = Note(0.125, "c", "Ноты/c0.wav")
d_8 = Note(0.125, "d", "Ноты/d0.wav")
e_8 = Note(0.125, "e", "Ноты/e0.wav")
f_8 = Note(0.125, "f", "Ноты/f0.wav")
g_8 = Note(0.125, "g", "Ноты/g0.wav")
a_8 = Note(0.125, "a", "Ноты/a0.wav")
h_8 = Note(0.125, "h", "Ноты/h0.wav")
# Определение шестнадцатых
c_h = Note(1 / 16, "c", "Ноты/c0.wav")
d_h = Note(1 / 16, "d", "Ноты/d0.wav")
e_h = Note(1 / 16, "e", "Ноты/e0.wav")
f_h = Note(1 / 16, "f", "Ноты/f0.wav")
g_h = Note(1 / 16, "g", "Ноты/g0.wav")
a_h = Note(1 / 16, "a", "Ноты/a0.wav")
h_h = Note(1 / 16, "h", "Ноты/h0.wav")


def add_to_bd(melody):
    # Получаем байты объекта
    b_object = pickle.dumps(melody)
    # Получаем название и путь мелодии
    name = melody.name.split("/")[-1]
    path = "/".join(melody.name.split("/")[:-1])
    con = sqlite3.connect("bd.sqlite")
    cur = con.cursor()
    # Записываем байты в БД
    cur.execute("""INSERT INTO melodies(id_user, name, path, object) VALUES(
                    (SELECT id_user FROM users where name = "{}"), "{}", "{}", ?)""".format(melody.user, name, path),
                (sqlite3.Binary(b_object),))
    con.commit()
    con.close()


class Melody:
    def __init__(self, name, user, pages):
        # Словарь, в котором хранятся списки нот по страницам
        self.pages = pages
        self.name = name
        self.user = user

    def save(self):
        total_snds = []
        for i in self.pages.keys():
            slov = {}
            # Создаем списки нот на одной y
            for j in self.pages[i]:
                if j.y not in slov.keys():
                    slov[j.y] = [j]
                else:
                    slov[j.y].append(j)
            snds = []
            # Соединение нот
            for j in sorted(list(slov.keys())):
                # Ноты сортируются по х и объединяются с добавлением тишины, зависящей от растояния между нотами
                line = sorted(slov[j], key=lambda s: s.x)
                snd = AudioSegment.silent(duration=10 * line[0].x) + line[0].sound
                X_pos = line[0].x
                for k in range(len(line[1:])):
                    snd = snd + AudioSegment.silent(duration=10 * (line[1:][k].x - X_pos)) + line[1:][k].sound
                    X_pos = line[1:][k].x
                snd = snd + AudioSegment.silent(duration=10 * (700 - X_pos))
                snds.append(snd)
            # В итоге получаем список, в котором хранятся 11 аудиосегментов и, чтобы ноты могли звучать одновременно,
            # накладываем их друг на друга
            try:
                snd_total = snds[0]
                for j in snds[1:]:
                    snd_total = snd_total.overlay(j)
                total_snds.append(snd_total)
            except IndexError:
                pass
        # Повторям для каждой страницы и объединяем
        melody = total_snds[0]
        for i in total_snds[1:]:
            melody = melody + i
        melody.export(self.name, format="wav")


class partiture_view(QtWidgets.QGraphicsView):
    def __init__(self, window):
        QtWidgets.QGraphicsView.__init__(self, window)
        self.setMouseTracking(True)
        self.window = window

    def mouseMoveEvent(self, event):
        # Определяем х и у, чтобы их можно было получить в главном классе
        x = event.x()
        y = event.y()
        self.x = x
        self.y = y

    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        self.x = x
        self.y = y
        self.item = self.itemAt(event.x(), event.y())
        # Если нажимается кнопка мыши в области, где находится нота, то она удаляется
        if event.button() == QtCore.Qt.LeftButton:
            # удаляем из сцены, а затем удаляем из списка нот
            self.scene().removeItem(self.item)
            for i in self.window.notes:
                # Удаление ноты происходит, если координаты нажатия подходят под расположение ноты
                if ((i.x - x) ** 2) ** 0.5 < 10 and ((i.y - y) ** 2) ** 0.5 < 30:
                    self.window.notes.remove(i)


class Ui_Choose_User_Form(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Ui_Choose_User_Form, self).__init__(parent)
        self.par = parent
        self.setWindowTitle("User dialog")
        self.resize(400, 300)
        self.label = QtWidgets.QLabel(self)
        self.label.setText("Введите имя пользователя")
        self.label.setGeometry(QtCore.QRect(110, 130, 191, 21))
        self.label.setObjectName("label")

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setGeometry(QtCore.QRect(110, 170, 191, 33))
        self.lineEdit.setObjectName("lineEdit")

        self.setName = QtWidgets.QPushButton(self)
        self.setName.setGeometry(QtCore.QRect(175, 210, 50, 50))
        self.setName.setText("Set")
        self.setName.clicked.connect(self.btn_set_clicked)

        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setGeometry(QtCore.QRect(50, 20, 321, 31))
        self.label_2.setObjectName("label_2")
        self.label_2.setText("Здравствуй, " + str(self.par.nick))

    def btn_set_clicked(self): 
        self.par.nick = self.lineEdit.text()             
        self.label_2.setText("Здравствуй, " + self.par.nick)


class Ui_Open_melody(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Ui_Open_melody, self).__init__(parent)
        self.connection = sqlite3.connect("bd.sqlite")
        self.resize(600, 500)
        self.cur = self.connection.cursor()
        self.parent = parent
        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setGeometry(QtCore.QRect(0, 110, 175, 290))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setRowCount(0)

        # Заполнение первой таблицы
        for i, row in enumerate(self.cur.execute("select name from users").fetchall()):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(str(elem)))

        self.tableWidget_2 = QtWidgets.QTableWidget(self)
        self.tableWidget_2.setGeometry(QtCore.QRect(280, 110, 471, 291))
        self.tableWidget_2.setObjectName("tableWidget_2")
        self.tableWidget_2.setColumnCount(1)
        self.tableWidget_2.setRowCount(0)
        self.tableWidget_2.setVisible(False)

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(0, 90, 180, 19))
        self.label.setObjectName("label")
        self.label.setText("Выберите пользователя")

        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setGeometry(QtCore.QRect(280, 80, 81, 19))
        self.label_2.setObjectName("label_2")
        self.label_2.setText("Мелодии пользователя")
        self.label_2.setVisible(False)

        self.button_set = QtWidgets.QPushButton(self)
        self.button_set.setGeometry(QtCore.QRect(50, 450, 50, 50))
        self.button_set.setText("Set")
        self.button_set.clicked.connect(self.btn_set_clicked)

        self.button_open = QtWidgets.QPushButton(self)
        self.button_open.setGeometry(QtCore.QRect(420, 450, 50, 50))
        self.button_open.setText("Open")
        self.button_open.clicked.connect(self.btn_open_clicked)

    def closeEvent(self, event):
        self.connection.close()

    def btn_set_clicked(self):
        # При выборе элемента из первой таблицы, 2-ая становится видна и тоже заполняется
        self.tableWidget_2.clear()
        self.tableWidget_2.setVisible(True)
        self.label_2.setVisible(True)
        name = self.tableWidget.selectedItems()[0].text()
        for i, row in enumerate(self.cur.execute(
                """select name from melodies where id_user = (select id_user from users where name = "{}")""".format(
                    name)).fetchall()):
            self.tableWidget_2.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget_2.setItem(i, j, QtWidgets.QTableWidgetItem(str(elem)))

    def btn_open_clicked(self):
        name = self.tableWidget_2.selectedItems()[0].text()
        b_obj = self.cur.execute("""select object from melodies where name = '{}'""".format(name)).fetchone()[0]
        # Получаем байты объекта базы данных и работаем с восстановленным объектом
        obj = pickle.loads(b_obj)
        # Ноты стираются с помощью метода next_page. Он, конечно, используется не для этого, но так как данные
        # после этого заменятся, то без разницы, что они где-то в промежутке сохранились
        self.parent.next_page()
        # Данные текщего объекта заменяются на данные полученного объекта
        self.parent.pages = obj.pages
        self.parent.num = 1
        self.parent.notes = obj.pages[1]
        self.parent.pushButton_4.setVisible(False)
        # Отрисовка рбъекта
        for i in self.parent.notes:
            item = QtWidgets.QGraphicsPixmapItem(self.parent.images_of_not[i.form])
            self.parent.scene.addItem(item)
            item.setPos(i.x, i.y)
        self.close()


# Дизайн главного окна
class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(700, 550)

        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(570, 490, 50, 50))
        self.pushButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Картинки/Play.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("Картинки/Play_pressed.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(50, 50))
        self.pushButton.setObjectName("pushButton")

        self.pushButton_2 = QtWidgets.QPushButton(Form)
        self.pushButton_2.setGeometry(QtCore.QRect(630, 490, 50, 50))
        self.pushButton_2.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("Картинки/Next.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap("Картинки/Next_pressed.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pushButton_2.setIcon(icon1)
        self.pushButton_2.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_2.setObjectName("pushButton_2")

        self.pushButton_3 = QtWidgets.QPushButton(Form)
        self.pushButton_3.setGeometry(QtCore.QRect(510, 490, 50, 50))
        self.pushButton_3.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("Картинки/save.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("Картинки/save.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pushButton_3.setIcon(icon2)
        self.pushButton_3.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_3.setObjectName("pushButton_3")

        self.pushButton_4 = QtWidgets.QPushButton(self)
        self.pushButton_4.setGeometry(QtCore.QRect(450, 490, 50, 50))
        self.pushButton_4.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("Картинки/previous.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap("Картинки/previous.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pushButton_4.setIcon(icon3)
        self.pushButton_4.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_4.setVisible(False)

        self.push_user = QtWidgets.QPushButton(self)
        self.push_user.setGeometry(QtCore.QRect(0, 0, 50, 50))
        self.push_user.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("Картинки/User.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4.addPixmap(QtGui.QPixmap("Картинки/User.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.push_user.setIcon(icon4)
        self.push_user.setIconSize(QtCore.QSize(50, 50))
        self.push_user.setObjectName("push_user")

        self.push_open = QtWidgets.QPushButton(self)
        self.push_open.setGeometry(QtCore.QRect(650, 0, 50, 50))
        self.push_open.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("Картинки/Open.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon5.addPixmap(QtGui.QPixmap("Картинки/Open.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.push_open.setIcon(icon5)
        self.push_open.setIconSize(QtCore.QSize(50, 50))
        self.push_open.setObjectName("push_open")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))


class Editor(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.initUI()
        # Создается сцена, в которой будут храниться объекты
        self.im = QPixmap("Картинки/partiture.svg")
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addPixmap(self.im)
        # Сцена отображается
        self.graphicsView = partiture_view(self)
        self.graphicsView.setGeometry(QtCore.QRect(0, 60, 700, 371))
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setScene(self.scene)

        self.coords = (0, 0)
        self.notes = []
        self.pages = {}
        # Номер страницы. Служит ключем для pages
        self.num = 1
        self.nick = "User111"
        # Картинки нот. Нужны для восстановления вида из объекта
        self.images_of_not = [QPixmap("Картинки/all_note.svg"), QPixmap("Картинки/half_note.svg"),
                              QPixmap("Картинки/half_note_down.svg"), QPixmap("Картинки/forth_note.svg"),
                              QPixmap("Картинки/forth_note_down.svg"), QPixmap("Картинки/eigth_note.svg"),
                              QPixmap("Картинки/eigth_note_down.svg"), QPixmap("Картинки/hex_note.svg"),
                              QPixmap("Картинки/hex_note_down.svg")]
        self.run()

    def initUI(self):
        self.setupUi(self)
        self.setWindowTitle("Нотный редактор")
        self.setMouseTracking(True)

    def save_dialog(self):
        fname = QFileDialog.getSaveFileName(self, 'Open file', '')
        return fname

    def open_dialog(self):
        open = Ui_Open_melody(self)
        open.exec()

    def keyPressEvent(self, event):
        # Получаем у и х из виджета
        y = self.graphicsView.y
        x = self.graphicsView.x
        # Сделано для упрощения кода
        statements = [y < 40, 40 <= y <= 80, 80 <= y <= 100, 100 <= y <= 130, 130 <= y <= 155, 155 <= y <= 190,
                      190 <= y <= 210, 210 <= y <= 240, 240 <= y <= 270, 270 <= y <= 300, y > 300]
        positions = [0, 30, 60, 90, 120, 145, 175, 205, 230, 260, 290]
        num = statements.index(True)

        if event.key() == QtCore.Qt.Key_1:
            notes = [g.change_ton(1.5), f, e, d, c, h.change_ton(0.66), a.change_ton(0.66), g.change_ton(0.66),
                     f.change_ton(0.66), e.change_ton(0.66), d.change_ton(0.66)]
            item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[0])
            self.scene.addItem(item)
            item.setPos(x - 20, positions[num])
            # Объект копируется, так как иначе ссылки идут на один и тот же объект, что приводит к багам
            note = copy(notes[num])
            note.x = x
            note.y = positions[num]
            self.notes.append(note)
        elif event.key() == QtCore.Qt.Key_2:
            notes = [g_2.change_ton(1.5), f_2, e_2, d_2, c_2, h_2.change_ton(0.66), a_2.change_ton(0.66),
                     g_2.change_ton(0.66), f_2.change_ton(0.66), e_2.change_ton(0.66), d_2.change_ton(0.66)]
            note = copy(notes[num])
            if y >= 175:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[1])
                note.form = 1
            else:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[2])
                note.form = 2
            self.scene.addItem(item)
            item.setPos(x - 20, positions[num])
            note.x = x
            note.y = positions[num]
            self.notes.append(note)
        elif event.key() == QtCore.Qt.Key_4:
            notes = [g_4.change_ton(1.5), f_4, e_4, d_4, c_4, h_4.change_ton(0.66), a_4.change_ton(0.66),
                     g_4.change_ton(0.66), f_4.change_ton(0.66), e_4.change_ton(0.66), d_4.change_ton(0.66)]
            note = copy(notes[num])
            if y >= 175:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[3])
                note.form = 3
            else:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[4])
                note.form = 4
            self.scene.addItem(item)
            item.setPos(x - 20, positions[num])
            note.x = x
            note.y = positions[num]
            self.notes.append(note)
        elif event.key() == QtCore.Qt.Key_8:
            notes = [g_8.change_ton(1.5), f_8, e_8, d_8, c_8, h_8.change_ton(0.66), a_8.change_ton(0.66),
                     g_8.change_ton(0.66), f_8.change_ton(0.66), e_8.change_ton(0.66), d_8.change_ton(0.66)]
            note = copy(notes[num])
            if y >= 175:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[5])
                note.form = 5
            else:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[6])
                note.form = 6
            self.scene.addItem(item)
            item.setPos(x - 20, positions[num])
            note.x = x
            note.y = positions[num]
            self.notes.append(note)
        elif event.key() == QtCore.Qt.Key_H:
            notes = [g_h.change_ton(1.5), f_h, e_h, d_h, c_h, h_h.change_ton(0.66), a_h.change_ton(0.66),
                     g_h.change_ton(0.66), f_h.change_ton(0.66), e_h.change_ton(0.66), d_h.change_ton(0.66)]
            note = copy(notes[num])
            if y >= 175:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[7])
                note.form = 7
            else:
                item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[8])
                note.form = 8
            self.scene.addItem(item)
            item.setPos(x - 20, positions[num])
            note.x = x
            note.y = positions[num]
            self.notes.append(note)
        self.update()

    def run(self):
        # В самом начале вызывается окно выбора пользователя, чтобы человек сразу получил имя. Иначе возникают
        # проблемы при добавлении в БД
        self.click_button_user(self)
        self.pushButton_3.clicked.connect(self.save)
        self.pushButton_2.clicked.connect(self.next_page)
        self.pushButton_4.clicked.connect(self.previous_page)
        self.pushButton.clicked.connect(self.play)
        self.push_user.clicked.connect(self.click_button_user)
        self.push_open.clicked.connect(self.open_dialog)

    def click_button_user(self, parent):
        user_dialog = Ui_Choose_User_Form(self)
        user_dialog.exec_()
        # В этом методе, помимо вызова класса, выполняется добавление пользователя в БД 
        con = sqlite3.connect("bd.sqlite")
        cur = con.cursor()
        users = [str(i[0]) for i in cur.execute("select name from users").fetchall()]
        if self.nick not in users:
            cur.execute("""INSERT INTO users(name) VALUES("{}")""".format(self.nick))
        con.commit()
        con.close()

    def save(self):
        # Вызывается диалог сохранения
        name = self.save_dialog()[0]
        # В словарь сохраняется последний список нот
        self.pages[self.num] = self.notes
        melody = Melody(name, self.nick, self.pages)
        melody.save()

        add_to_bd(melody)

    def play(self):
        self.pages[self.num] = self.notes
        pages = {1: self.notes}
        # Создается и проигрывается временный файл, который потом удаляется
        Melody("tmp_file____1.wav", "Kayram", pages).save()
        wave = sa.WaveObject.from_wave_file("tmp_file____1.wav")
        play_obj = wave.play()
        play_obj.wait_done()
        os.remove("tmp_file____1.wav")

    def next_page(self):
        # В словарь сохраняется последний список нот
        self.pages[self.num] = self.notes
        self.num += 1
        # Удаляются объекты со сцены
        for i in self.graphicsView.items():
            self.scene.removeItem(i)
        self.scene.addPixmap(self.im)
        if self.num not in self.pages.keys():
            self.notes = []
        else:
            self.notes = self.pages[self.num]
        # Включаются кнопка Previous
        self.pushButton_4.setVisible(True)

    def previous_page(self):
        # Удаляются объкты со сцены
        for i in self.graphicsView.items():
            self.scene.removeItem(i)
        self.scene.addPixmap(self.im)
        self.pages[self.num] = self.notes
        self.num -= 1
        if self.num == 1:
            self.pushButton_4.setVisible(False)
        try:
            self.notes = self.pages[self.num]
        except KeyError:
            pass
        # Отрисовка нот с предыдущей страницы словаря
        for i in self.notes:
            item = QtWidgets.QGraphicsPixmapItem(self.images_of_not[i.form])
            self.scene.addItem(item)
            item.setPos(i.x, i.y)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Editor()
    ex.show()
    sys.exit(app.exec())
