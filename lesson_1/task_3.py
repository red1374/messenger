from tabulate import tabulate

from utils import ping_interface, TextColor
from task_2 import host_ping_range


def host_range_ping_tab(pings):
    """ Function to print out a pings list in a table view """
    if not pings:
        print(f'{TextColor.RED}Empty pings list')
        return False

    # Split pings dict for two lists
    unreachable = []
    reachable = []
    for ip, state in pings.items():
        if state:
            unreachable.append(ip)
        else:
            reachable.append(ip)

    print(tabulate({'Reachable': tuple(sorted(reachable, key=lambda ip: int(ip))),
                    'Unreachable': tuple(sorted(unreachable, key=lambda ip: int(ip)))},
                   headers='keys', tablefmt="pipe"))


if __name__ == '__main__':
    pings_dict = {}
    ip_start, ip_count = ping_interface()
    host_ping_range(ip_start, ip_count, pings_dict)
    host_range_ping_tab(pings_dict)
