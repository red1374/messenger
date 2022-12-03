import os
import sys

from sqlalchemy import Column, Integer, String, DateTime, func, create_engine, Text
from sqlalchemy.orm import sessionmaker, declarative_base

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import SERVER_DATABASE

Base = declarative_base()


class ClientDatabase:
    """ Client side database """
    class Users(Base):
        """ Users table """
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        username = Column(String(50), unique=True)

        def __init__(self, name):
            self.username = name

        def __repr__(self):
            return "<User('%s')>" % self.username

    class Messages(Base):
        """ User Messages table """
        __tablename__ = 'messages'
        id = Column(Integer, primary_key=True)
        from_user = Column(String)
        to_user = Column(String)
        message = Column(Text)
        date = Column(DateTime(timezone=True), server_default=func.now())

        def __init__(self, from_user, to_user, message):
            self.from_user = from_user
            self.to_user = to_user
            self.message = message

        def __repr__(self):
            return "<Message('%s', '%s', '%s')>" % (self.from_user, self.to_user, self.message)

    class Contacts(Base):
        """ User contacts list table """
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user = Column(String, unique=True)

        def __init__(self, name):
            self.user = name

        def __repr__(self):
            return "<Contact('%s')>" % self.user

    def __init__(self, name):
        # Create connection
        self.engine = create_engine(f'sqlite:///client_{name}_db.sqlite',
                                    echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})
        # Create all tables
        Base.metadata.create_all(self.engine)
        session = sessionmaker(bind=self.engine)

        self.session = session()

        # Truncate user contacts table
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """ Add new user contact """
        if not self.session.query(self.Contacts).filter_by(user=contact).count():
            new_contact = self.Contacts(contact)
            self.session.add(new_contact)
            self.session.commit()

    def del_contact(self, contact):
        """ Delete user contact """
        record = self.session.query(self.Contacts).filter_by(user=contact)
        if record.count():
            record.delete()
            self.session.commit()

    def add_users(self, users_list):
        """ Add users from server to client users table. Remove old users before insert """
        self.session.query(self.Users).delete()
        for user in users_list:
            new_user = self.Users(user)
            self.session.add(new_user)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        """ Save user message """
        new_message = self.Messages(from_user, to_user, message)
        self.session.add(new_message)
        self.session.commit()

    def get_contacts(self):
        """ Get contacts list """
        return [contact[0] for contact in self.session.query(self.Contacts.user).all()]

    def get_users(self):
        """ Get users list """
        return [user[0] for user in self.session.query(self.Users.username).all()]

    def check_user(self, user):
        """ Check if user exists in a Users table """
        if self.session.query(self.Users).filter_by(username=user).count():
            return True

        return False

    def check_contact(self, contact):
        """ Check if user exists in a Contacts table """
        if self.session.query(self.Contacts).filter_by(user=contact).count():
            return True

        return False

    def get_history(self, from_who=None, to_who=None):
        """ Get messages list """
        query = self.session.query(self.Messages)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query - query.filter_by(to_user=to_who)

        return [(message.from_user, message.to_user, message.message, message.date)
                for message in query.all()]

    def contacts_clear(self):
        """ Clear user contacts table """
        self.session.query(self.Contacts).delete()


if __name__ == '__main__':
    client = ClientDatabase('test_1')

    for user in ['test_2', 'test_3', 'test_4']:
        client.add_contact(user)
    client.add_contact('test_4')


