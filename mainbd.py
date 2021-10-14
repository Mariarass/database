import sys
import re
import MySQLdb
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QPushButton, QWidget, QApplication, QColorDialog, QFontDialog, QFileDialog
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QTableWidgetItem as QWT
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QPropertyAnimation, QRect,QDate
Form, _ = uic.loadUiType("md.ui")
Form2, _ = uic.loadUiType("mysql.ui")
Form3, _ = uic.loadUiType("procedure.ui")
Form4, _ = uic.loadUiType("params.ui")
Form5, _ = uic.loadUiType("internet.ui")
Form6, _ = uic.loadUiType("auth.ui")


class Auth(QtWidgets.QWidget, Form6):
    """
    Вход пользователей
    """
    getting_info = QtCore.pyqtSignal(list)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.send_info)

    def send_info(self):
        """
        Отправляем инфу
        :return:
        """
        check = self.check_auth()
        user = self.lineEdit_2.text()
        password = self.lineEdit.text()
        if check:  # если логин пароль верен
            list_values = [user, password]  # заносим их в список
            self.getting_info.emit(list_values)  # и отправляем
            self.close()  # и закрываем

    def check_auth(self):
        """
        Проверка логина пароля
        :return:
        """
        user = self.lineEdit_2.text()
        password = self.lineEdit.text()
        try:
            MySQLdb.connect(user=user, passwd=password,
                            charset="utf8", db="mysql")  # подключение к бд

            return True

        except MySQLdb._exceptions.OperationalError as sql:
            sql = eval(str(sql))[0]
            if sql == 1044:
                return True
            QMessageBox.critical(self, "Ошибка", "Логин или пароль неверны!")
            return False


# Виджет для выбора баз майскл
class ProcedureParams(QtWidgets.QWidget, Form4):
    """
    Окно параметров
    """
    getting_info = QtCore.pyqtSignal(list)

    def __init__(self, data):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.data = data
        self.print_table()
        self.pushButton.clicked.connect(self.send_info)

    def send_info(self):
        len_rows = len(self.data)
        list_values = []
        for item in range(len_rows):
            value = self.tableWidget.cellWidget(item, 2).text()  # беру инфу из лайнедита
            if value:  # если лайнедит содержит что то
                list_values.append(value)  # то заносим это что то в список

        if len_rows != len(list_values):  # Если строк и количесивр данных из лайнедита не равны, то ничё не делаем
            return

        self.getting_info.emit(list_values)  # Отправляем инфу
        self.close()

    def print_table(self):
        """
        В тблвиджет создаем два поля и третее поля как лайнедит
        :return:
        """
        len_rows = len(self.data)
        len_cols = len(self.data[1]) + 1
        self.tableWidget.setRowCount(len_rows)
        self.tableWidget.setColumnCount(len_cols)

        for j in range(len_rows):
            for i in range(len_cols):
                try:
                    self.tableWidget.setItem(j, i, QWT(str(self.data[j + 1][i])))
                except (
                        KeyError,
                        IndexError):  # когда два столбца переберутся возникнет ошибка и так мы создадим лайнедит
                    self.tableWidget.setCellWidget(j, i, QtWidgets.QLineEdit())


class ProcedureMenu(QtWidgets.QWidget, Form3):
    """
    Окно процедур
    """
    getting_info = QtCore.pyqtSignal(list)  # Переменная будет выступать слотом для класса МайВин

    def __init__(self, cursor, db):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.procedure_name = ""
        self.cursor = cursor
        self.cursor.execute('show procedure status')

        items = [procedure[1] for procedure in cursor if procedure[0] == db]
        self.listWidget.addItems(items)

        self.pushButton.clicked.connect(self.check_params)
        self.listWidget.currentTextChanged.connect(self.currentTextChanged)
        self.listWidget.itemDoubleClicked.connect(self.check_params)

    def run(self, params=None):
        """
        Выбираем процедуру для показа
        :param params:
        :return:
        """
        list_info = [self.procedure_name]
        if params:
            list_info.append(params)

        self.getting_info.emit(list_info)  # Отправляем послание
        self.close()

    def currentTextChanged(self, procedure_name):
        """
        При клике на любую процедуру выводится инфа
        :param procedure_name: процедура на которую кликнули
        :return:
        """
        self.cursor.execute("SHOW CREATE PROCEDURE " + procedure_name)
        data = self.cursor.fetchall()
        procedure_text = str(data[0][2])
        self.plainTextEdit.setPlainText(procedure_text)

    def check_params(self):
        """
        Проверяем процедурки на наличие параметров
        :return:
        """
        self.procedure_name = self.listWidget.currentItem().text()
        self.cursor.execute(
            f"SELECT * FROM information_schema.parameters WHERE SPECIFIC_NAME = '{self.procedure_name}'")  # (('def', 'new_db', 'spisokzp', 1, 'IN', 'inp1', 'int', None, None, 10, 0, None, None, 'int(11)', 'PROCEDURE')
        data = self.cursor.fetchall()

        # todo эту ***** в тот класс чтобы отрендерить несколько строк для вхожных даанных.
        count_params = 0
        info = {}

        if data:  # если данные о процедуре есть
            for item in data:  # перебираем каждый параметр процедуру
                if item[4] == "IN":  # если параметр IN
                    count_params += 1  # Увеличиваем значение
                    info[item[3]] = [item[5], item[
                        6]]  # Это словарь. Ключ item[3] значение - список из двух элементов. Выглядит типа того: item[3] = 1, item[5] = inp1, item[6] = int

        if not count_params:  # если параметров нет то
            self.run()  # поехали
            return False
        else:  # иначе открываем меню параметров
            self.params_menu = ProcedureParams(info)
            self.params_menu.getting_info.connect(self.grab_info_params)
            self.params_menu.show()

    # Ловим инфу из ProcedureParams
    @QtCore.pyqtSlot(list)
    def grab_info_params(self, params):
        self.run(params)


class MySqlAuth(QtWidgets.QWidget, Form2):
    """
    Окно для выбора локальной базы
    """
    getting_info = QtCore.pyqtSignal(list)  # Переменная будет выступать слотом для класса МайВин

    def __init__(self, cursor, user_password):  # Получаем данные которые мы передали из MyWin
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.user_password = user_password
        cursor.execute('show databases')
        for db in cursor:
            self.listWidget.addItem(db[0])
        self.pushButton.clicked.connect(self.open_db)

    def open_db(self):
        """
        Открывает базу по нажатию кнопки
        :return:
        """
        params = []
        db = self.listWidget.currentItem().text()
        params.append(db)
        params.append('localhost')

        check = self.check_auth(params)
        if check:  # если все правильно то
            self.getting_info.emit(params)  # Отправляем инфу в главное окно
            self.close()

    def check_auth(self, params):
        """
        Проверяем правльность введнных данных
        :param params:
        :return:
        """
        try:
            MySQLdb.connect(user=self.user_password[0], passwd=self.user_password[1],
                            charset="utf8", db=params[0])  # подключение к бд
            return True

        except MySQLdb._exceptions.OperationalError as err:
            code = eval(str(err))[0]
            if code == 1044:
                QMessageBox.critical(self, "Ошибка", "Пользователь не имеет права просматривать эту базу!")
            else:
                QMessageBox.critical(self, "Ошибка", "Логин или пароль неверны!")
            return False


class Internet(QtWidgets.QWidget, Form5):
    """
    Окно для входа в удаленную базу данных
    """
    getting_info = QtCore.pyqtSignal(list)  # Переменная будет выступать слотом для класса МайВин

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        # Просто база в инете для примера
        self.lineEdit.setText("remotemysql.com")
        self.lineEdit_2.setText("Xf6qN0vpa1")
        self.lineEdit_3.setText("3adreavF4w")
        self.lineEdit_4.setText("3adreavF4w")

        self.pushButton.clicked.connect(self.run)

    def run(self):

        host = self.lineEdit.text()
        password = self.lineEdit_2.text()
        user = self.lineEdit_3.text()
        db = self.lineEdit_4.text()

        try:

            MySQLdb.connect(user=user, password=password,
                            host=host,
                            database=db)

            params = [user, password, db, host]

            self.getting_info.emit(params)  # Отправляем инфу в главное окно проги (MyWin)
            self.close()

        except MySQLdb._exceptions.OperationalError as err:
            code = eval(str(err))[0]
            if code == 2005:
                QMessageBox.critical(self, "Ошибка", "Выбранный хост не найден")
            if code == 1045:
                QMessageBox.critical(self, "Ошибка", "Пользователь или пароль введён неверно")
            if code == 1044:
                QMessageBox.critical(self, "Ошибка", "База данных с таким названием не найдена")


class MyWin(QtWidgets.QMainWindow, Form):
    """
    Главное окно программы
    """

    def __init__(self, parent=None):

        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.window_text = "DBEditor"  # Название программы
        self.setWindowTitle(self.window_text)  # Применяем название программы

        # Два словаря для работы как с локальным так и с удаленным подключением баз
        self.current_db = {"user": "", "password": "", "db": "information_schema", 'host': 'localhost'}
        self.current_db_local = {"user": "", "password": "", "db": "information_schema", 'host': 'localhost'}

 


        self.pushButton_3.clicked.connect(lambda: self.run(1))
        self.pushButton_4.clicked.connect(lambda: self.run(2))
        self.pushButton.clicked.connect(lambda: self.run(3))
        self.pushButton_5.clicked.connect(lambda: self.run(4))
  
        self.pushButton_29.clicked.connect(lambda:self.AnimationObject(self.frame_13, 200))
        self.pushButton_25.clicked.connect(lambda:self.AnimationObject2(self.frame, 200))
                                         
        self.pushButton_2.clicked.connect(self.open_mysql)
        self.pushButton_26.clicked.connect(self.open_procedure)
        self.pushButton_6.clicked.connect(self.open_mysql_global)
        self.pushButton_27.clicked.connect(self.auth)
        self.comboBox.currentTextChanged.connect(self.xD)
        self.column = 0
        self.s=0
        self.s2=0
        self.pushButton_26.setEnabled(False)

          # По умолчанию процедуры не доступны
        self.state_buttons(True)  # и кнопки тоже

    def connect_db(self):
        """
        Подключение базы к питону
        :return: возращает курсор и коннект чтобы работать с ними из друггих функций
        """
        try:
            con = MySQLdb.connect(user=self.current_db["user"], passwd=self.current_db["password"],
                                  charset="utf8", db=self.current_db["db"],
                                  host=self.current_db["host"])  # подключение к бд

            return con, con.cursor()

        except MySQLdb._exceptions.OperationalError as sql:
            sql = eval(str(sql))[
                0]  # Переводим ошибку в строку, потом в кортеж, чтобы разбить ошибку на две части - код ошибки и текст ошибки
            if sql == 1045:
                QMessageBox.information(self, "Информация",
                                        "Пользователь не выбран. Сейчас вам нужно ввести имя пользвоателя и пароль для доступа к базам данным")
                self.auth()
                return False  # Без ретерна иногда зацикливалось всё

    def run(self, num):
        """
        Функция обновляет, добавляет, удаляет данные из базы и таблицы а также работает с запросами
        :param num:
        """
        try:
            con, cur = self.connect_db()
            curr_index = self.comboBox.currentText()
            cur.execute(f"select* from `{curr_index}`")

            if num == 0:  # вывод данных при открытии программы
                result = cur.fetchall()
                self.fill_table(result, cur)
            elif num == 1:  # ВСТАВКА
                count_rows = self.tableWidget.rowCount() - 1
                count_columns = self.tableWidget.columnCount()
                field_names = tuple(i[0] for i in cur.description)
                field_names = "(" + "".join(i + "," for i in field_names)[:-1] + ")"
                values = []
                try:
                    for column in range(count_columns):
                        values.append(
                            self.tableWidget.item(count_rows, column).text())  # считывание значений для добавления
                except AttributeError:
                    QMessageBox.critical(self, "Ошибка", "Не все поля были заполнены для добавления")
                    return

                if len(values) == 1:  # Если столбец всего один, то нужно values без tuple указывать
                    cur.execute(f"INSERT INTO `{curr_index}` {field_names} VALUES ({values[0]})")
                else:
                    cur.execute(f"INSERT INTO `{curr_index}` {field_names} VALUES {tuple(values)}")
                self.tableWidget.insertRow(count_rows + 1)  # добавление новой строки в виджет

            elif num == 2:  # УДАЛЕНИЕ
                field_name = tuple(i[0] for i in cur.description)[0]  # Имя первого столбца
                selectedRows = self.tableWidget.selectionModel().selectedRows()  # Получаем индекс выделенных строк
                try:
                    int(len(self.tableWidget.selectedItems()) / len(selectedRows))
                except ZeroDivisionError:
                    QMessageBox.critical(self, "Ошибка", "Вы не выбрали строки для удаления!")

                for row in range(len(selectedRows)):  # Цикл по выдленным строкам
                    try:
                        value = self.tableWidget.item(selectedRows[0].row(), 0).text()
                        cur.execute(
                            f'DELETE FROM `{curr_index}` WHERE {field_name}={value}')  # Удаялем из базы

                        self.tableWidget.removeRow(selectedRows[0].row())  # Удаляем из таблицы строку
                        selectedRows = self.tableWidget.selectionModel().selectedRows()  # Обноляем выделенные строки, ведь одна выделенная удалилась выше
                    except AttributeError:
                        pass

            elif num == 3:  # ЗАПРОС
                txt = self.lineEdit.text()
                try:
                    cur.execute(txt)
                    self.state_buttons()  # блочим кнопки чтобы в результат запроса не могли добавить удалить итд
                    self.fill_table(cur.fetchall())

                except (MySQLdb._exceptions.ProgrammingError, MySQLdb._exceptions.OperationalError):
                    QMessageBox.critical(self, "Ошибка", "Неверно введен запрос!")

            elif num == 4:  # ОБНОВЛЕНИЕ
                try:
                    current_row = self.tableWidget.selectedIndexes()[-1].row()  # Узнаем индекс выделенной строки
                except IndexError:
                    QMessageBox.information(self, "Информация",
                                            "Для обновление записи нужно ее выделить левой кнопкой мыши")
                    return  # прекращаем выполнение функции run

                count_columns = self.tableWidget.columnCount()
                values = []
                field_names = tuple(i[0] for i in cur.description)
                query = f"update `{curr_index}` set "
                for column in range(count_columns):
                    try:
                        values.append(
                            self.tableWidget.item(current_row, column).text())  # считывание значений для добавления
                        query += f'{field_names[column]}="{values[column]}",'
                    except AttributeError:
                        QMessageBox.critical(self, "Ошибка", "Не все поля были заполнены для обновления")
                        return

                result = cur.fetchall()

                try:
                    if curr_index == "emp":  # У emp просто первичный ключ был вторым столбиком а не первым, поэтому вынесено
                        query = query[:-1] + f" where {field_names[1]} = {result[current_row][1]} "
                    else:
                        query = query[:-1] + f" where {field_names[0]} = {result[current_row][0]} "
                except IndexError:
                    QMessageBox.critical(self, "Ошибка",
                                         "Для обновления данной записи вам необходимо её сначало добавить")
                    return
                cur.execute(query)
                QMessageBox.about(self, "Успешно ", "Запись изменена!")

            con.commit()
            con.close()
            self.set_headers(cur)

        except Exception as err:  # Exception чтобы использовать err
            sql_code = eval(str(err))[0]  # Код ошибки Мускула
            text_error = eval(str(err))[1]  # Текст ошибки мускула

            if sql_code == 1366 or sql_code == 1292:
                value = re.findall(r"value: '([^\']*)", text_error)[
                    0]  # Ищем какое значение неправильное, через регулярные выражения
                column = re.findall(r"column '([^\']*)", text_error)[0]  # Ищем в какой калонке неправильное значение
                QMessageBox.critical(self, "Ошибка", f"Некорректное значение `{value}` для столбца `{column}`")
            elif sql_code == 1062:
                value = re.findall(r"entry '([^\']*)", text_error)[0]
                QMessageBox.critical(self, "Ошибка", f"Первичный ключ со значением {value} уже существует!")
            elif sql_code == 1264:
                text_error = eval(str(err))[1]
                column = re.findall(r"column '([^\']*)", text_error)[0]
                QMessageBox.critical(self, "Ошибка", f"Слишком больше значение для поля {column}")
            elif sql_code == 1451 or sql_code == 1452:
                text_error = eval(str(err))[1]
                column = re.findall(r"fails \(([^]]+)\)", text_error)[0]
                QMessageBox.critical(self, "Ошибка",
                                     f"Невозможно удалить или обновить запись: ограничение внешнего ключа\n {column}")
            elif sql_code == 2013:
                QMessageBox.critical(self, "Ошибка", "Потеряно соединение с MySQL сервером")
            elif sql_code == 1265:
                QMessageBox.critical(self, "Ошибка", "Неверные данные для обновления")
            elif sql_code == 1227:
                QMessageBox.critical(self, "Ошибка",
                                     "Доступ запрещен для просмотра этой БД (отсутствуют права для просмотра)")
            elif sql_code == 1103:
                QMessageBox.critical(self, "Ошибка",
                                     "База данных не имеет таблиц")

            else:  # else для отлова ошибок кторых нет выше
                print(err)

    def fill_table(self, data, cur=None):
        """
        Вывод дааных в таблицу
        :param data: данные
        :param cur: курсор, нужен когда таблица пустая например и нужно посчитать столбцы
        :return:
        """
        try:
            self.tableWidget.clear()
            if not data:  # Если данных нет (таблица пустая)
                field_names = tuple(i[0] for i in cur.description)  # Узнаем столбцы
                len_rows = 1  # Делаем 1 чтобы можно было заполнять эту пустую таблицу
                len_columns = len(field_names)
                self.tableWidget.setRowCount(len_rows)
                self.tableWidget.setColumnCount(len_columns)
                self.set_headers(cur)
            else:
                len_rows = len(data)
                len_columns = len(data[0])
                self.tableWidget.setRowCount(len_rows + 1)
                self.tableWidget.setColumnCount(len_columns)
                for row in range(len_rows):
                    for column in range(len_columns):
                        value = str(data[row][column])
                        self.tableWidget.setItem(row, column, QWT(value))
        except AttributeError:  # Процедура ничего выводит если
            pass

    def get_tables(self, cur):
        """
        Узнаем все таблицы из базы чтобы засунуть их в комбобохс
        :param cur: через курсор узнаём их собственно
        :return:
        """
        self.comboBox.blockSignals(
            True)  # Не позволяет выполняться сигналу self.comboBox.currentTextChanged.connect(self.xD) который в init у нас, если бы не этот метод
        # то при каждом добавлении в комбобокс через метод addItems(ниже) сигнал бы срабатывал и вызывалась бы функции xD которая обновляет данные в таблице

        self.comboBox.clear()  # очищаем комбик, нужно при включении новой базы и вследстве этого удаления старых таблиц
        cur.execute("SHOW TABLES")
        result = cur.fetchall()
        tables = [table[0] for table in result]  # Список таблиц
        self.comboBox.addItems(tables)
        self.comboBox.blockSignals(False)  # Разблочиваем чтобы сигнал снова стал работать
        self.run(0)  # При запуске базы выводим сразу первую таблицу

    def set_headers(self, cur):
        """
        Задаёт заголовки для таблиц
        :param cur: принимает курсор в качестве параметра
        """
        try:
            field_names = [i[0] for i in cur.description]
            column_count = len(field_names)
            self.tableWidget.setColumnCount(column_count)
            self.tableWidget.setHorizontalHeaderLabels(field_names)
            header = self.tableWidget.horizontalHeader()

            header.setSectionResizeMode(column_count - 1, QtWidgets.QHeaderView.Stretch)

        except TypeError:
            pass

    def xD(self):
        """
        Когда меняем комбобокс, данные из таблицы автоматом грузятся
        """
        self.state_buttons(block=False)
        self.run(0)

    def checker_procedure(self, cur):
        """
        Проверяем есть ли процедуры в базе
        :param cur:
        :return:
        """
        cur.execute('show procedure status')
        items = [procedure[1] for procedure in cur if procedure[0] == self.current_db['db']]
        if not items:  # если нет процедур
             self.pushButton_26.setEnabled(False)  # Блочим кнопку процедуры, ведь их же нет, воот
        else:
             self.pushButton_26.setEnabled(True)

    def state_buttons(self, block=True):
        if block:  # блочим
            self.pushButton.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)
            self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        else:  # разблочим
            self.pushButton.setEnabled(True)
            self.pushButton_3.setEnabled(True)
            self.pushButton_4.setEnabled(True)
            self.pushButton_5.setEnabled(True)
            self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)

    def auth(self):
        """
        Открывает окно входа пользователя
        :return:
        """
        self.AnimationObject(self.frame_13, 200)
        self.authentication = Auth()
        self.authentication.getting_info.connect(self.grab_info_auth)
        self.authentication.show()

    def open_procedure(self):
        """
        Открывет окно выбора процедур
        :return:
        """
        self.AnimationObject(self.frame_13, 200)
        self.AnimationObject2(self.frame, 200)
        try:
            _, cur = self.connect_db()
            self.procedure_win = ProcedureMenu(cur, self.current_db['db'])
            self.procedure_win.getting_info.connect(self.grab_info_procedure)
            self.procedure_win.show()
        except MySQLdb._exceptions.OperationalError:
            print('error')

    def open_mysql(self):
        """
        Открывает окно выбора локальной БД
        :return:
        """
        self.AnimationObject2(self.frame, 200)
        self.AnimationObject(self.frame_13, 200)
        self.current_db = self.current_db_local.copy()  # В current db заносим инфу из local, нужно потому что если последний вход был в базу через инет, то инфа будет именно об интернет логине и пароле
        try:
            con, cur = self.connect_db()
            user_password = [self.current_db['user'], self.current_db['password']]
            self.mysql_win = MySqlAuth(cur, user_password)  # создаём обьект нашего виджет-клаасса
            self.mysql_win.getting_info.connect(self.grab_info_mysql)  # делаем сигнал когда вызывается ф-я граб инфо
            self.mysql_win.show()  # виводим наш втджет
            
        except TypeError:
            return

    def open_mysql_global(self):
        """
        Открывает окно подключение к удаленной бД
        :return:
        """
        self.AnimationObject(self.frame_13, 200)
        self.mysql_internet = Internet()  # создаём обьект нашего виджет-клаасса
        self.mysql_internet.getting_info.connect(
            self.grab_info_mysql_internet)  # делаем сигнал когда вызывается ф-я граб инфо
        self.mysql_internet.show()  # виводим наш втджет

    # Ловим инфу из окна удаленного выбора базы
    @QtCore.pyqtSlot(list)
    def grab_info_mysql_internet(self, db_info):  # дб нэйм наше послание ок да
        self.tableWidget.clear()
        self.current_db['user'] = db_info[0]
        self.current_db['password'] = db_info[1]
        self.current_db['db'] = db_info[2]
        self.current_db['host'] = db_info[3]
        _, cur = self.connect_db()
        self.lineEdit.setText("")
        self.get_tables(cur)
        self.checker_procedure(cur)

    # Ловим инфу из окна локального выбора базы
    @QtCore.pyqtSlot(list)
    def grab_info_mysql(self, db_info):
        self.tableWidget.clear()
        self.current_db['db'] = db_info[0]
        self.current_db['host'] = db_info[1]
        _, cur = self.connect_db()
        self.lineEdit.setText("")  # Делаем строку запроса пустой
        self.get_tables(cur)  # Названия столбиков в таблвиджете
        self.state_buttons(False)  # Разблокируем кнопки ведь в таблицах мы можем делать добавления и тд
        self.checker_procedure(cur)  # Проверка наличия процедур у базы

    # Ловим инфу из окна выбора процедур
    @QtCore.pyqtSlot(list)
    def grab_info_procedure(self, procedure_name):
        con, cur = self.connect_db()
        params = ""
        try:
            if len(procedure_name) == 1:  # если процедура без параметров
                cur.execute(f"call {procedure_name[0]}")
            else:  # иначе
                query = f"call {procedure_name[0]}"
                for item in range(len(procedure_name[1])):
                    params += f"'{procedure_name[1][item]}',"

                params = params[:-1]
                query += "({})".format(params)
                cur.execute(query)

            data = cur.fetchall()

            self.fill_table(data)  # Выводим инфу в таблицу
            self.set_headers(cur)  # Выводим заголовки колонок в таблицу
            header = self.tableWidget.horizontalHeader()

            try:
                column_count = len(data[0])

                if column_count >= 6:  # если колонок больше 6 то расстягиваем так
                    for i in range(column_count):
                        if i == column_count - 1:
                            header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
                        else:
                            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

                else:  # Иначе так
                    header.setSectionResizeMode(column_count - 1, QtWidgets.QHeaderView.Stretch)

            except IndexError:  # Если колонок нет
                self.tableWidget.setRowCount(1)

            self.state_buttons()  # блочим кнопки ведь выведятся процедуры

        except MySQLdb._exceptions.OperationalError:  # не помню
            self.tableWidget.clear()

    # Ловим инфу из окна выбора пользователя
    @QtCore.pyqtSlot(list)
    def grab_info_auth(self, info):
        # Заполняем инфу
        self.current_db['user'] = info[0]
        self.current_db['password'] = info[1]
        self.current_db_local['user'] = info[0]
        self.current_db_local['password'] = info[1]

        # Очищаем таблицы кнопки блочим
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)
        self.comboBox.clear()
        self.state_buttons()

        # Меняем наверху имя текущего юзера
        self.setWindowTitle(f"{self.window_text}. Пользователь: {info[0]}")

    def AnimationObject(self, widget: QtCore.QObject, duration: int):
            if self.s==0:
                rect=QtCore.QRect(0, 0, 461, 700)
                self.s+=1
            else:
                rect=QtCore.QRect(0, 0, 51, 31)
                self.s=0
            self.anim = QPropertyAnimation(widget, b"geometry")
            self.anim.setDuration(duration)
            self.anim.setStartValue(widget.rect())
            self.anim.setEndValue(rect)
            self.anim.start()
    def AnimationObject2(self, widget: QtCore.QObject, duration: int):
            
            if self.s2==0:
                rect=QtCore.QRect(0, 50, 461, 300)
                self.s2+=1
            else:
                rect=QtCore.QRect(0,0, 0, 0)
                self.s2=0
            self.anim = QPropertyAnimation(widget, b"geometry")
            self.anim.setDuration(duration)
            self.anim.setStartValue(widget.rect())
            self.anim.setEndValue(rect)
            self.anim.start()
def qt_message_handler(mode, context, message):
    if mode == QtCore.QtInfoMsg:
        mode = 'INFO'
    elif mode == QtCore.QtWarningMsg:
        mode = 'WARNING'
    elif mode == QtCore.QtCriticalMsg:
        mode = 'CRITICAL'
    elif mode == QtCore.QtFatalMsg:
        mode = 'FATAL'
    else:
        mode = 'DEBUG'
    print('qt_message_handler: line: %d, func: %s(), file: %s' % (
        context.line, context.function, context.file))
    print('  %s: %s\n' % (mode, message))


if __name__ == "__main__":
    QtCore.qInstallMessageHandler(qt_message_handler)
    app = QtWidgets.QApplication(sys.argv)
    myapp = MyWin()
    myapp.show()
    sys.exit(app.exec_())
