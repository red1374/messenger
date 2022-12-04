Common package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

Скрипт deceators.py
---------------

.. automodule:: common.decorators
	:members:
	
Скрипт descriptors.py
---------------------

.. autoclass:: common.descriptors.CheckPort
    :members:
   
Скрипт errors.py
---------------------
   
.. automodule:: common.errors
   :members:
   :undoc-members:
   :show-inheritance:
   
Скрипт metaclass.py
-----------------------

.. autoclass:: common.metaclass.DictChecker
   :members:

.. autoclass:: common.metaclass.ClientVerifier
   :members:
   
.. autoclass:: common.metaclass.ServerVerifier
   :members:
   
Скрипт utils.py
---------------------

common.utils. **get_params** ()


    Разбирает параметры командной строки и возвращает в виде словаря

common.utils. **get_message** (client)


	Функция приёма сообщений от удалённых компьютеров. Принимает сообщения JSON,
	декодирует полученное сообщение и проверяет что получен словарь.

common.utils. **send_message** (sock, message)


	Функция отправки словарей через сокет. Кодирует словарь в формат JSON и отправляет через сокет.


Скрипт variables.py
---------------------

Содержит разные глобальные переменные проекта.