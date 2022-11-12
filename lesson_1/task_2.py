from utils import ping_interface, print_result
from task_1 import host_ping


def host_ping_range(start_ip, qty_ip, pings):
    """ Function to start threads for each ip address from a given range """
    if not start_ip or not qty_ip:
        return False

    # Get ips range
    hosts_list = tuple((str(start_ip + index) for index in range(qty_ip)))

    host_ping(hosts_list, pings)


if __name__ == '__main__':
    pings_dict = {}
    ip_start, ip_count = ping_interface()
    host_ping_range(ip_start, ip_count, pings_dict)
    print_result(pings_dict)
