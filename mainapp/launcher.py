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
process_params = {'ip': DEFAULT_IP_ADDRESS, 'p': DEFAULT_PORT, 'n': ''}

while True:
    ACTION = input('Select an action:\n\tq - quit,\n\ts - start server and clients,\n\tx - kill all processes: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        # Start server process
        start_process('server', process_list=process_list)

        # Start clients processes
        for i in range(CLIENTS_COUNT):
            process_params['n'] = f'test_{i}'
            start_process('client', params=process_params, process_list=process_list)
        print(process_list)
    elif ACTION == 'x':

        while process_list:
            process = process_list.pop()
            process.kill()
