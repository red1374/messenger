import datetime
import os
import sys

from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
sys.path.append(os.path.join(os.getcwd(), '..'))


from common.variables import SERVER_DATABASE

Base = declarative_base()


class Storage:
    class Users(Base):
        """ Table with registered users """
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String(50), unique=True)
        last_login = Column(DateTime(timezone=True))  # , onupdate=func.now()

        def __init__(self, name):
            self.name = name
            self.last_login = datetime.datetime.now()

        def __repr__(self):
            return "<User('%s','%s')>" % (self.name, self.last_login)

    class ActiveUsers(Base):
        """ Table with user activity information """
        __tablename__ = 'users_activity'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'), unique=True)
        ipaddress = Column(String(50))
        port = Column(Integer)
        login_time = Column(DateTime(timezone=True), server_default=func.now())

        def __init__(self, user, ip, port):
            self.user = user
            self.ipaddress = ip
            self.port = port

        def __repr__(self):
            return "<User('%s','%s', '%s', '%s')>" % (self.user, self.ipaddress, self.port, self.login_time)

    class LoginHistory(Base):
        """ Table with users login information """
        __tablename__ = 'users_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        ipaddress = Column(String(50))
        port = Column(Integer)
        date_time = Column(DateTime(timezone=True), server_default=func.now())

        def __init__(self, user, ip, port):
            self.user = user
            self.ipaddress = ip
            self.port = port

        def __repr__(self):
            return "<User('%s','%s', '%s', '%s')>" % (self.user, self.ipaddress, self.port, self.date_time)

    def __init__(self):
        # Create connection
        self.engine = create_engine(SERVER_DATABASE,
                                    echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})
        # Create all tables
        Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)

        self.session = session()

        # Truncate table with active users
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ipaddress, port):
        """ Add an information about new connected user """

        result = self.session.query(self.Users).filter_by(name=username)

        # Add a record to a Users' table about new connected user
        if result.count():
            # Update last login time if user is already exists
            user = result.first()
            user.last_login = datetime.datetime.now()
        else:
            # Add new user
            user = self.Users(username)
            self.session.add(user)

        self.session.commit()

        # Add information about new active user
        user_activity = self.ActiveUsers(user.id, ipaddress, port)
        self.session.add(user_activity)

        # Add new record at history table
        user_history = self.LoginHistory(user.id, ipaddress, port)
        self.session.add(user_history)

        self.session.commit()

    def user_logout(self, username):
        """ Trigger function on user disconnect event """

        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        """ Get all registered users """
        users = self.session.query(self.Users.name, self.Users.last_login)
        return users.all()

    def active_users_list(self):
        """ Get a list of active users """
        users = self.session.query(
            self.Users.name,
            self.ActiveUsers.ipaddress,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.Users)

        return users.all()

    def login_history(self, username=''):
        """ Get information about current user or about all users """
        query = self.session.query(
            self.Users.name,
            self.LoginHistory.ipaddress,
            self.LoginHistory.port,
            self.LoginHistory.date_time
        ).join(self.Users)

        if username:
            query = query.filter(self.Users.name == username)

        return query.all()


# Tests
if __name__ == '__main__':
    test_db = Storage()
    test_db.user_login('Clinet 1', '192.168.0.1', 8080)
    test_db.user_login('Clinet 2', '192.168.0.2', 8081)

    print(test_db.active_users_list())
    print(test_db.login_history())

    test_db.user_logout('Clinet 1')

    print(test_db.active_users_list())
    print(test_db.login_history())

    print(test_db.users_list())
