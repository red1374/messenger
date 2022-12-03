import subprocess

from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS


def start_process(script_name, params={}, process_list=[]):
    """
    Create system process with given params
    :param script_name: - script file to execute
    :param params: - additional params
    :return: process object
    """
    if script_name == '':
        return None

    param = ''
    if params:
        for key, value in params.items():
            param += f' -{key} {value}' if value else ''

    new_process = subprocess.Popen(f'python {script_name}.py{param}', creationflags=subprocess.CREATE_NEW_CONSOLE)
    if new_process is not None:
        process_list.append(new_process)


process_list = []
CLIENTS_COUNT = 2
DEMO_PASSWORD = '123456'
process_params = {'ip': DEFAULT_IP_ADDRESS, 'port': DEFAULT_PORT, 'name': ''}

while True:
    ACTION = input('Select an action:\n\tq - quit,\n\ts - start server,\n\t'
                   'c - start clients,\n\t'
                   'x - kill all processes: ')

    if ACTION == 'q':
        # -- Exit launcher program ---------------------------
        break
    elif ACTION == 's':
        # -- Starting server process -------------------------
        start_process('server', process_list=process_list)
    elif ACTION == 'c':
        # -- Starting clients processes ----------------------
        try:
            client_count = int(input('Input test clients count.\n\t'
                                     f' {CLIENTS_COUNT} users must be already registered'
                                     f' on the server with password "{DEMO_PASSWORD}":\n\t'))
        except Exception as e:
            client_count = CLIENTS_COUNT

        process_params['p'] = DEMO_PASSWORD
        for i in range(client_count):
            process_params['name'] = f'test_{i}'
            start_process('client', params=process_params, process_list=process_list)
    elif ACTION == 'x':
        # -- Kill all the processes -------------------------
        while process_list:
            process = process_list.pop()
            process.kill()
