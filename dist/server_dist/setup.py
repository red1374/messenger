from setuptools import setup, find_packages

setup(name='server_messanger',
      version='1.2',
      description='Server part',
      packages=find_packages(),
      author_email='red13_74@mail.ru',
      author='Pleshakov Sergey',
      install_requeres=['PyQt5', 'sqlalchemy', 'pycruptodome', 'pycryptodomex'],
      scripts=['server/server_run'],
)
