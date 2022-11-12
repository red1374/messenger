from threading import Thread
from utils import ping_interface, threader, process_queues, print_result


def host_ping(hosts_list, pings):
    """ Function to start threads for each ip address """
    if not len(hosts_list):
        return False

    # Start all threads for each ip address
    for index in range(len(hosts_list)):
        t = Thread(target=threader, args=(hosts_list, pings))
        t.daemon = True
        t.start()

    # Fill in the queue with ip address position at hosts_list
    for worker in range(len(hosts_list)):
        process_queues.put(worker)

    # Join a queue to a main thread
    process_queues.join()


if __name__ == '__main__':
    pings_dict = {}

    ip_start, ip_count = ping_interface()

    # Get list of ips to ping
    hosts_list = tuple((str(ip_start + index) for index in range(ip_count)))

    # Start ping process
    host_ping(hosts_list, pings_dict)

    print_result(pings_dict)
