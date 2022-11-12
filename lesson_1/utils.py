from copy import copy
from ipaddress import ip_network, ip_address
import platform
from queue import Queue
from subprocess import Popen, PIPE
from threading import Lock


class TextColor:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'


def threader(hosts_list, pings):
    """ Check a queue for a new value and start a ping function """
    while True:
        worker = process_queues.get()
        params = copy(command)
        params[len(params) - 1] = hosts_list[worker]
        ping(params, pings)
        process_queues.task_done()


def ping(params, pings):
    """ Ping a host and save ping state to global var """

    ip = params[len(params) - 1]
    proc = Popen(params, stdout=PIPE, stderr=PIPE)

    # Lock this section, until we get a complete chunk then free it
    with thread_lock:
        proc.wait(3)
        pings[ip_address(ip)] = proc.returncode


def ping_interface():
    hosts_list = {}

    """ User interface function to get start ip address and ip addresses count """
    while True:
        ip = input('Input starting ip address: ')

        try:
            ip_start = ip_address(ip)
        except ValueError:
            print('Wrong ip address format. Try again')
        else:
            break

    while True:
        try:
            ip_count = int(input('Input ip addresses count: '))
        except ValueError:
            print('Input integer value')
        else:
            last_ip = ip_start + ip_count
            network = ip_network(f'{ip_start}/255.255.255.0', strict=False)
            if last_ip not in network:
                network_mask = str(network.network_address)[:-1:]
                start = int(str(ip_start).replace(network_mask, ''))
                print(f'Wrong ip addresses count. Max value is {255 - start}')
                continue
            break

    return ip_start, ip_count


def print_result(pings, sort_by_key=True):
    """ Function prints out colored pings list sorted by ips values """
    if not pings:
        print('Empty result list')
        return False

    ips_dict = {}
    if sort_by_key:
        # int() converts ip address object to decimal representation to sort properly
        ips_dict = dict(sorted(pings.items(), key=lambda item: int(item[0])))
    else:
        ips_dict = pings

    for ip, state in ips_dict.items():
        print(f'{TextColor.YELLOW}{str(ip):<15}: ', end='')
        if state:
            print(f'{TextColor.RED}is unreachable')
        else:
            print(f'{TextColor.GREEN}is reachable')

    return True


param = "-n" if platform.system().lower() == 'windows' else "-c"
wait = "-w" if platform.system().lower() == 'windows' else "-W"
command = ["ping", param, "1", wait, '150', '']

process_queues = Queue()
thread_lock = Lock()
