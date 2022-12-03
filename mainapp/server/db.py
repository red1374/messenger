import datetime
import os
import sys
from select import select

from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey, create_engine, Text
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
        passwd_hash = Column(String(50), unique=True)
        pubkey = Column(Text, unique=True)

        def __init__(self, name, passwd_hash):
            self.name = name
            self.last_login = datetime.datetime.now()
            self.passwd_hash = passwd_hash

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
        __tablename__ = 'users_login_history'
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
            return "<History('%s','%s', '%s', '%s')>" % (self.user, self.ipaddress, self.port, self.date_time)

    class UsersContacts(Base):
        """ Table with users contacts """
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        contact = Column(ForeignKey('users.id'))

        def __init__(self, user, contact):
            self.user = user
            self.contact = contact

        def __repr__(self):
            return "<Contact('%s','%s')>" % (self.user, self.contact)

    class UsersHistory(Base):
        """ Table with users messages statistics """
        __tablename__ = 'users_history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user, sent=0, accepted=0):
            self.user = user
            self.sent = sent
            self.accepted = accepted

        def __repr__(self):
            return "<History('%s','%s','%s')>" % (self.user, self.sent, self.accepted)

    def __init__(self, db_path):
        # Create connection
        self.engine = create_engine('sqlite:///' + (db_path if db_path else SERVER_DATABASE),
                                    echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})
        # Create all tables
        Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)

        self.session = session()

        # Truncate table with active users
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ipaddress, port, key):
        """ Add an information about new connected user """

        result = self.session.query(self.Users).filter_by(name=username)

        # -- Add a record to a Users' table about new connected user -
        if result.count():
            # -- Update last login time if user is already exists -----
            user = result.first()
            user.last_login = datetime.datetime.now()
            # -- Save public key if it was changed --------------------
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('User is not registered')

        # -- Add information about new active user --------------------
        user_activity = self.ActiveUsers(user.id, ipaddress, port)
        self.session.add(user_activity)

        # -- Add new record at history table --------------------------
        login_history = self.LoginHistory(user.id, ipaddress, port)
        self.session.add(login_history)

        self.session.commit()

    def user_logout(self, username):
        """ Trigger function on user disconnect event """

        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def add_user(self, name, passwd_hash):
        """ Add new user method """
        new_user = self.Users(name, passwd_hash)
        self.session.add(new_user)
        self.session.commit()

        history_row = self.UsersHistory(new_user.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        """ Remove user method """
        user = self.session.query(self.Users).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        """ Get user password hash method """
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """ Get user public key method """
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        """ Check user exists method """
        if self.session.query(self.Users).filter_by(name=name).count():
            return True
        return False

    def users_list(self):
        """ Get all registered users """
        users = self.session.query(self.Users.name, self.Users.last_login)
        return users.all()

    def get_contacts(self, username):
        """ Get users contacts list """
        user = self.session.query(self.Users).filter_by(name=username).one()

        # -- Get users contacts list -----------------
        query = self.session.query(self.UsersContacts, self.Users.name). \
            filter_by(user=user.id). \
            join(self.Users, self.UsersContacts.contact == self.Users.id)

        # -- Return only usernames -------------------
        return [contact[1] for contact in query.all()]

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

    def process_message(self, sender, recipient):
        """ Update user's messages statistic """
        sender_id = self.session.query(self.Users).filter_by(name=sender).first().id
        recipient_id = self.session.query(self.Users).filter_by(name=recipient).first().id

        # -- Update user's messages statistics --------------------
        sender_stat = self.session.query(self.UsersHistory).filter_by(user=sender_id).first()
        sender_stat.sent += 1
        recipient_stat = self.session.query(self.UsersHistory).filter_by(user=recipient_id).first()
        recipient_stat.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        """ Add new user contact """
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        # -- Check if this contact is already exists
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return False

        # -- Add new contact
        new_contact = self.UsersContacts(user.id, contact.id)
        self.session.add(new_contact)
        self.session.commit()

    def remove_contact(self, user, contact):
        """ Remove contact from users contacts """
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        if not contact:
            return False

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete()

        self.session.commit()

    def message_history(self):
        """ Get users messages statistics """
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted,
        ).join(self.Users)

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
