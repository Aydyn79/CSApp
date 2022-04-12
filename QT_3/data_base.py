import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///declarative_style_base.db3', echo=False)

Base = declarative_base()


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



Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
sess = Session()

sess.query(Active_Users).delete()
sess.commit()


# Функция выполняющаяся при входе пользователя, записывает в базу факт входа
def user_login(username, ip_address, port):
    print()
    print(username, ip_address, port)
    # Запрос в таблицу пользователей на наличие там пользователя с таким именем
    rez = sess.query(All_Users).filter_by(name=username)

    # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
    if rez.count():
        user = rez.first()
        user.login_time = datetime.datetime.now()
    # Если нет, то создаём нового пользователя
    else:
        # Создаём экземпляр класса self.AllUsers, через который передаём данные в таблицу
        user = All_Users(username)
        sess.add(user)
        # Коммит здесь нужен для того, чтобы создать нового пользователя,
        # id которого будет использовано для добавления в таблицу активных пользователей
        sess.commit()

    # Теперь можно создать запись в таблицу активных пользователей о факте входа.
    # Создаём экземпляр класса self.ActiveUsers, через который передаём данные в таблицу
    new_active_user = Active_Users(user.id, ip_address, port, datetime.datetime.now())
    sess.add(new_active_user)

    # Создаём экземпляр класса self.LoginHistory, через который передаём данные в таблицу
    history = Login_History(user.id, datetime.datetime.now(), ip_address, port)
    sess.add(history)

    # Сохраняем изменения
    sess.commit()


# Функция, фиксирующая отключение пользователя
def user_logout(username):
    # Запрашиваем пользователя, что покидает нас
    # получаем запись из таблицы self.AllUsers
    user = sess.query(All_Users).filter_by(name=username).first()
    # Удаляем его из таблицы активных пользователей.
    # Удаляем запись из таблицы self.ActiveUsers
    sess.query(Active_Users).filter_by(user=user.id).delete()
    # Применяем изменения
    sess.commit()


# Функция возвращает список известных пользователей со временем последнего входа.
def users_list():
    # Запрос строк таблицы пользователей.
    query = sess.query(
        All_Users.name,
        All_Users.login_time
    )
    # Возвращаем список кортежей
    return query.all()


# Функция возвращает список активных пользователей
def active_users_list(username=None):
# def active_users_list():
    # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
    query = sess.query(
            All_Users.name,
            Active_Users.ip_address,
            Active_Users.port,
            Active_Users.login_time
        ).join(All_Users)
        # Возвращаем список кортежей
    if username:
        query = query.filter(All_Users.name != username)
        # Возвращаем список активных пользователей за исключением пользователя запросившего этот список
        # print(query.all())
    return query.all()


# Функция, возвращающая историю входов по пользователю или всем пользователям
def login_history(username=None):
    # Запрашиваем историю входа
    query = sess.query(All_Users.name,
                               Login_History.date_time,
                               Login_History.ip,
                               Login_History.port
                               ).join(All_Users)
    # Если было указано имя пользователя, то фильтруем по этому имени
    if username:
        query = query.filter(All_Users.name == username)
    # Возвращаем список кортежей
    return query.all()




# if __name__ == '__main__':
    # user = All_Users("ДжавахарлалНеру")
    # sess.add(user)
    # sess.commit()
    # user_login('Agent_Dogget','125.126.23.56','7756')
    # user_logout('Agent_Dogget')
    # print(users_list())
    # user_login('ДжавахарлалНеру', '128.126.28.58', '7856')
    print(active_users_list())
    # user_logout('ДжавахарлалНеру')
    # user_login('ДжавахарлалНеру', '128.126.28.58', '7856')
    # print(login_history('ДжавахарлалНеру'))
