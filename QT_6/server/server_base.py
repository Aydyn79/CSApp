import datetime
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
sys.path.append('../../')


# engine = create_engine('sqlite:///server_base.db3', echo=False)

Base = declarative_base()

path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'../server_base.db3')

class Server_db:
    # Класс - описание таблиц сервера
    class All_Users(Base):
        __tablename__ = 'all_users'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        login_time = Column(DateTime)

        def __init__(self, name):
            self.id = None
            self.name = name
            self.login_time = datetime.datetime.now()

        def __repr__(self):
            return f'<User({self.name}, last login {self.login_time})>'

    class Active_Users(Base):
        __tablename__ = 'active_users'
        id = Column('id', Integer, primary_key=True)
        user = Column('user', ForeignKey('all_users.id'), unique=True)
        ip_address = Column('ip_address', String)
        port = Column('port', Integer)
        login_time = Column('login_time', DateTime)

        def __init__(self, user_id, ip_address, port, date):
            self.id = None
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = date

        def __repr__(self):
            return f'<User({self.user} last login {self.login_time} from address {self.ip_address})>'

    class Login_History(Base):
        __tablename__ = 'login_history'
        id = Column('id', Integer, primary_key=True)
        name = Column('name', ForeignKey('all_users.id'))
        date_time = Column('date_time', DateTime)
        ip = Column('ip', String)
        port = Column('port', String)

        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

        def __repr__(self):
            return f'<User({self.name} last login {self.date_time} from address {self.ip} and port {self.port})>'

    # Класс - отображение таблицы контактов пользователей
    class Users_Contacts(Base):
        __tablename__ = 'users_contacts'
        id = Column('id', Integer, primary_key=True)
        user = Column('user', ForeignKey('all_users.id'))
        contact = Column('contact', ForeignKey('all_users.id'))

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Класс отображение таблицы истории действий
    class Users_History(Base):
        __tablename__ = 'users_history'
        id = Column('id', Integer, primary_key=True)
        user = Column('user', ForeignKey('all_users.id'))
        sent = Column('sent', Integer)
        accepted = Column('accepted', Integer)

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

        # Конструктор класса:

    def __init__(self, path):
        print(path)
        self.database_engine = create_engine(f'sqlite:///{path}',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        Base.metadata.create_all(self.database_engine)
        Session = sessionmaker(bind=self.database_engine)
        self.sess = Session()

        self.sess.query(self.Active_Users).delete()
        self.sess.commit()

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.sess.query(self.All_Users).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.sess.query(self.All_Users).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.sess.query(self.All_Users).filter_by(name=name).count():
            return True
        else:
            return False


    # Функция выполняющаяся при входе пользователя, записывает в базу факт входа
    def user_login(self, username, ip_address, port):
        print()
        print(username, ip_address, port)
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        rez = self.sess.query(self.All_Users).filter_by(name=username)

        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if rez.count():
            user = rez.first()
            user.login_time = datetime.datetime.now()
        # Если нет, то создаём нового пользователя
        else:
            # Создаём экземпляр класса self.AllUsers, через который передаём данные в таблицу
            user = self.All_Users(username)
            self.sess.add(user)
            # Коммит здесь нужен для того, чтобы создать нового пользователя,
            # id которого будет использовано для добавления в таблицу активных пользователей
            self.sess.commit()
            user_in_history = self.Users_History(user.id)
            self.sess.add(user_in_history)

        # Теперь можно создать запись в таблицу активных пользователей о факте входа.
        # Создаём экземпляр класса self.ActiveUsers, через который передаём данные в таблицу
        new_active_user = self.Active_Users(user.id, ip_address, port, datetime.datetime.now())
        self.sess.add(new_active_user)

        # Создаём экземпляр класса self.LoginHistory, через который передаём данные в таблицу
        history = self.Login_History(user.id, datetime.datetime.now(), ip_address, port)
        self.sess.add(history)

        # Сохраняем изменения
        self.sess.commit()

    # Функция, фиксирующая отключение пользователя
    def user_logout(self, username):
        # Запрашиваем пользователя, что покидает нас
        # получаем запись из таблицы self.AllUsers
        user = self.sess.query(self.All_Users).filter_by(name=username).first()
        # Удаляем его из таблицы активных пользователей.
        # Удаляем запись из таблицы self.ActiveUsers
        self.sess.query(self.Active_Users).filter_by(user=user.id).delete()
        # Применяем изменения
        self.sess.commit()

    # Функция возвращает список известных пользователей со временем последнего входа.
    def users_list(self):
        # Запрос строк таблицы пользователей.
        query = self.sess.query(
            self.All_Users.name,
            self.All_Users.login_time
        )
        # Возвращаем список кортежей
        return query.all()

    # Функция возвращает список активных пользователей
    def active_users_list(self, username=None):
        # def active_users_list():
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        query = self.sess.query(
            self.All_Users.name,
            self.Active_Users.ip_address,
            self.Active_Users.port,
            self.Active_Users.login_time
        ).join(self.All_Users)
        # Возвращаем список кортежей
        # if username:
        #     query = query.filter(self.All_Users.name != username)
        #     # Возвращаем список активных пользователей за исключением пользователя запросившего этот список
        #     print(query.all())
        return query.all()

    # Функция, возвращающая историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        # Запрашиваем историю входа
        query = self.sess.query(self.All_Users.name,
                                self.Login_History.date_time,
                                self.Login_History.ip,
                                self.Login_History.port
                                ).join(self.All_Users)
        # Если было указано имя пользователя, то фильтруем по этому имени
        if username:
            query = query.filter(self.All_Users.name == username)
        # Возвращаем список кортежей
        return query.all()

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        # Получаем ID отправителя и получателя
        sender = self.sess.query(self.All_Users).filter_by(name=sender).first().id
        recipient = self.sess.query(self.All_Users).filter_by(name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.sess.query(self.Users_History).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.sess.query(self.Users_History).filter_by(user=recipient).first()
        recipient_row.accepted += 1
        self.sess.commit()

    # Функция добавляет контакт для пользователя.
    def add_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.sess.query(self.All_Users).filter_by(name=user).first()
        contact = self.sess.query(self.All_Users).filter_by(name=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.sess.query(self.Users_Contacts).filter_by(user=user.id, contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = self.Users_Contacts(user.id, contact.id)
        self.sess.add(contact_row)
        self.sess.commit()

    # Функция удаляет контакт из базы данных
    def remove_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.sess.query(self.All_Users).filter_by(name=user).first()
        contact = self.sess.query(self.All_Users).filter_by(name=contact).first()
        # Проверяем существование контакта
        if not contact:
            return
        # Удаление контакта
        print(self.sess.query(self.Users_Contacts).filter(
            self.Users_Contacts.user == user.id,
            self.Users_Contacts.contact == contact.id
        ).delete())
        self.sess.commit()

    # Функция возвращает список контактов пользователя.
    def get_contacts(self, username):
        # Запрашиваем указанного пользователя
        user = self.sess.query(self.All_Users).filter_by(name=username).one()

        # Запрашиваем его список контактов
        query = self.sess.query(self.Users_Contacts, self.All_Users.name). \
            filter_by(user=user.id). \
            join(self.All_Users, self.Users_Contacts.contact == self.All_Users.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    # Функция возвращает количество переданных и полученных сообщений
    def message_history(self):
        query = self.sess.query(
            self.All_Users.name,
            self.All_Users.login_time,
            self.Users_History.sent,
            self.Users_History.accepted
        ).join(self.All_Users)
        # Возвращаем список кортежей
        return query.all()

if __name__ == '__main__':
    test_db = Server_db(path)
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    print(test_db.users_list())


# user = All_Users("ДжавахарлалНеру")
# sess.add(user)
# sess.commit()
# user_login('Agent_Dogget','125.126.23.56','7756')
# user_logout('Agent_Dogget')
# print(users_list())
# user_login('ДжавахарлалНеру', '128.126.28.58', '7856')
# print(active_users_list())
# user_logout('ДжавахарлалНеру')
# user_login('ДжавахарлалНеру', '128.126.28.58', '7856')
# print(login_history('ДжавахарлалНеру'))

# test_db = ServerStorage('server_base.db3')
# test_db.user_login('1111', '192.168.1.113', 8080)
# test_db.user_login('McG2', '192.168.1.113', 8081)
# pprint(test_db.users_list())
# pprint(test_db.active_users_list())
# test_db.user_logout('McG2')
# pprint(test_db.login_history('re'))
# test_db.add_contact('test2', 'test1')
# test_db.add_contact('test1', 'test3')
# test_db.add_contact('test1', 'test6')
# test_db.remove_contact('test1', 'test3')
# test_db.process_message('McG2', '1111')
# pprint(test_db.message_history())
