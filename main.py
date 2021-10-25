"""
NTP-client

Author: Danylo Zemlianyi
Run with admin rights
If timeout error, use another server from the list:
    0.ua.pool.ntp.org
    1.ua.pool.ntp.org
    2.ua.pool.ntp.org
    3.ua.pool.ntp.org
    ntp.time.in.ua
"""
import sys
from threading import *
import socket
import struct
import time
import datetime
import win32api


# Class for NTP packet
class NTPPacket:
    _FORMAT = "!B B b b 11I"

    def __init__(self, version_number=4, mode=3, transmit=float(0)):
        self.leap_indicator = 0
        self.version_number = version_number
        self.mode = mode
        self.stratum = 0
        self.pool = 0
        self.precision = 0
        self.root_delay = 0
        self.root_dispersion = 0
        self.ref_id = 0
        self.reference = 0
        self.originate = 0
        self.receive = 0
        self.transmit = transmit

    def pack(self):
        return struct.pack(NTPPacket._FORMAT,
                           (self.leap_indicator << 6) +
                           (self.version_number << 3) + self.mode,
                           self.stratum,
                           self.pool,
                           self.precision,
                           int(self.root_delay) + get_fraction(self.root_delay, 16),
                           int(self.root_dispersion) +
                           get_fraction(self.root_dispersion, 16),
                           self.ref_id,
                           int(self.reference),
                           get_fraction(self.reference, 32),
                           int(self.originate),
                           get_fraction(self.originate, 32),
                           int(self.receive),
                           get_fraction(self.receive, 32),
                           int(self.transmit),
                           get_fraction(self.transmit, 32))

    def unpack(self, data: bytes):
        unpacked_data = struct.unpack(NTPPacket._FORMAT, data)

        self.leap_indicator = unpacked_data[0] >> 6  # 2 bits
        self.version_number = unpacked_data[0] >> 3 & 0b111  # 3 bits
        self.mode = unpacked_data[0] & 0b111  # 3 bits

        self.stratum = unpacked_data[1]  # 1 byte
        self.pool = unpacked_data[2]  # 1 byte
        self.precision = unpacked_data[3]  # 1 byte

        # 2 bytes | 2 bytes
        self.root_delay = (unpacked_data[4] >> 16) + \
                          (unpacked_data[4] & 0xFFFF) / 2 ** 16
        # 2 bytes | 2 bytes
        self.root_dispersion = (unpacked_data[5] >> 16) + \
                               (unpacked_data[5] & 0xFFFF) / 2 ** 16

        # 4 bytes
        self.ref_id = str((unpacked_data[6] >> 24) & 0xFF) + " " + \
                      str((unpacked_data[6] >> 16) & 0xFF) + " " + \
                      str((unpacked_data[6] >> 8) & 0xFF) + " " + \
                      str(unpacked_data[6] & 0xFF)

        self.reference = unpacked_data[7] + unpacked_data[8] / 2 ** 32  # 8 bytes
        self.originate = unpacked_data[9] + unpacked_data[10] / 2 ** 32  # 8 bytes
        self.receive = unpacked_data[11] + unpacked_data[12] / 2 ** 32  # 8 bytes
        self.transmit = unpacked_data[13] + unpacked_data[14] / 2 ** 32  # 8 bytes

        return self


# Convert variables to necessary format
def get_fraction(number, precision):
    return int((number - int(number)) * 2 ** precision)


# Get the time of local system
def get_system_time():
    return time.time()


# Get the time from NTP server
def get_ntp_time():
    packet = NTPPacket(version_number=2, mode=3, transmit=time.time() + FORMAT_DIFF)
    answer = NTPPacket()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(WAITING_TIME)
        s.sendto(packet.pack(), (server, port))
        data = s.recv(48)
        answer.unpack(data)
    return answer.transmit - FORMAT_DIFF


# Updating system time
def update_system_time():
    server_time = get_ntp_time()
    server_ms = round(server_time % 1 * 1000)
    system_time = get_system_time()
    print("Current server time:", time.ctime(server_time), round(server_time % 1 * 1000), "ms")
    print("Current system time:", time.ctime(system_time), round(system_time % 1 * 1000), "ms")
    system_tuple = time.localtime(system_time)
    server_tuple = time.localtime(server_time)
    print("Correcting...")
    # server_tuple.tm_hour - TIMEZONE_OFFSET is for timezone offset of Windows
    # print((system_tuple.tm_year, system_tuple.tm_mon, system_tuple.tm_wday, system_tuple.tm_mday,
    #        server_tuple.tm_hour - TIMEZONE_OFFSET, server_tuple.tm_min, server_tuple.tm_sec, server_ms))
    win32api.SetSystemTime(system_tuple.tm_year, system_tuple.tm_mon, system_tuple.tm_wday, system_tuple.tm_mday,
                           server_tuple.tm_hour - TIMEZONE_OFFSET, server_tuple.tm_min, server_tuple.tm_sec, server_ms)
    print("System time updated!")
    system_time = get_system_time()
    print("Current system time:", time.ctime(system_time), round(system_time % 1 * 1000), "ms")


# Checking offset for given time (in seconds)
def check_for_offset(interval):
    print("Checking offset for {} seconds".format(interval))
    update_system_time()
    print("Sleeping for {} seconds...".format(interval))
    time.sleep(interval)
    server_time = get_ntp_time()
    system_time = get_system_time()
    offset = round(abs(server_time-system_time) % 1 * 1000)
    print("Current server time:", time.ctime(server_time), round(server_time % 1 * 1000), "ms")
    print("Current system time:", time.ctime(system_time), round(system_time % 1 * 1000), "ms")
    print("Time offset for {} seconds is {} ms".format(interval, offset))


def sync_time():
    global SYNC
    while 1:
        if F:
            break
        if SYNC:
            update_system_time()
            time.sleep(5)


# Setting up server info
print("NTP-client\n")
FORMAT_DIFF = (datetime.date(1970, 1, 1) - datetime.date(1900, 1, 1)).days * 24 * 3600
WAITING_TIME = 2
TIMEZONE_OFFSET = 3
server = "0.ua.pool.ntp.org"
port = 123

# Main code
SYNC = False
F = False
t1 = Thread(target=sync_time)
t1.start()
while True:
    command = str(input("Print 1 to start sync, 0 to stop, OFFSET to measure offset, EXIT to close the program: "))
    if command == "1" and SYNC:
        print("Sync is already started")
    elif command == "0" and not SYNC:
        print("Sync is not initialized")
    elif command == "1":
        print("Starting time sync...")
        SYNC = True
    elif command == "0":
        print("Wait...")
        SYNC = False
        time.sleep(5)
        print("Time sync is over")
    elif command == "OFFSET":
        SYNC = False
        time.sleep(1)
        wait_for = int(input("Enter the interval for measurement: "))
        check_for_offset(wait_for)
    elif command == "EXIT":
        F = True
        sys.exit(0)
