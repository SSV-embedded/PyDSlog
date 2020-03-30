"""
  ____          ____   ____   _                         ____  ____ __     __ 
 |  _ \  _   _ |  _ \ / ___| | |  ___    __ _          / ___|/ ___|\ \   / / 
 | |_) || | | || | | |\___ \ | | / _ \  / _` |  _____  \___ \\___ \ \ \ / /  
 |  __/ | |_| || |_| | ___) || || (_) || (_| | |_____|  ___) |___) | \ V / 
 |_|     \__, ||____/ |____/ |_| \___/  \__, |         |____/|____/   \_/ 
         |___/                          |___/                     

"""
"""
from PyDSlog.crc8 import crc8
import serial
import struct

class STM_stream:

    def __init__(self, sz_block, channels_to_use, frequency, port, baudrate, n_frame=100):

        self.channels = channels_to_use
        self.port = port

        try:
            self.sz_block = int(sz_block)
            self.baudrate = int(baudrate)
            self.n_frame = int(n_frame)
            self.frequency = int(frequency)
        except Exception as e:
            raise e

        if self.sz_block <= 0:
            raise ValueError("Frame size / sz_block is 0 or negative")

        if self.baudrate <= 0:
            raise ValueError("baudrate is 0 or negative")

        if self.frequency <= 0:
            raise ValueError("frequency is 0 or negative")
        self.con = None

        if len(self.channels) == 0:
            raise IndexError("no channels selected")

        if self.sz_block <= self.n_frame:
            self.n_frame = self.sz_block

        self.n_channels = len(self.channels)
        self.read_qty = 2 + (self.n_channels * 2)  # Calculate expected bytes to read

        self.write_timeout = 1
        self.read_timeout = ((self.read_qty * self.n_frame) / self.frequency) + 1

    def connect(self):

        try:
            self.con = serial.Serial(self.port, self.baudrate, write_timeout=self.write_timeout,
                                     timeout=self.read_timeout)
        except (IOError, serial.SerialException) as e1:
            raise e1
        except ValueError as e2:
            raise e2

    def disconnect(self):

        self.con.close()

    def start(self):

        n_chan = 0

        chan = {"C1": 1, "C2": 2, "C3": 4, "C4": 8, "C5": 16, "C6": 32, "C7": 64, "C8": 128}

        start_flag = "A"
        chan_in = 0

        for n in self.channels:
            for j in chan.keys():
                if (n == j):
                    chan_in = (chan_in | chan[j])  # set bits in variable ports_in for the selected ports to use
                    n_chan = n_chan + 1  # counter n_ports

        f_upper = (self.frequency >> 8) & 0xff  # upper
        f_lower = self.frequency & 0xff  # lower

        f_max = 11520 / ((2 * n_chan) + 3)  # Calculate max frequency

        if f_max < self.frequency:
            raise NameError(
                "Frequency is too high for selected quantity of channels")  # if the selected frequency is higher to f_max, 
            # then print alert

        arr = [ord(start_flag), chan_in, f_lower, f_upper]  # put everything in one list

        b_arr = bytearray(arr)  # bytearray from list

        hash = crc8()  # crc8
        hash.update(b_arr)  # crc with buff
        crc_val = hash.digest()  # read crc value
        b_arr = b_arr + crc_val  # add crc_val to the end of the bytearray

        try:
            self.con.write(b_arr)  # write buff with streaming settings
        except serial.SerialTimeoutException as e:
            raise e

    def stop(self):

        try:

            for i in range(0, 512):  # send 512 times "z" to stop the streaming mode
                self.con.write(b"\x5A")

        except serial.SerialTimeoutException as e:
            raise e

    def read(self, transpose=False):

        f = str(self.n_channels) + "h"  # h for the format integer. see python struct formats

        if transpose:
            ret = [[0 for j in range(self.n_channels)] for i in range(self.sz_block)]  # use list
        else:
            ret = [[0 for j in range(self.sz_block)] for i in range(self.n_channels)]

        count = 0  # counter. If this counter has the value of sz_block, 
        # then we are ready and return N-array with values

        while 1:  # loop

            buff = self.con.read(self.read_qty * self.n_frame)  # read (self.read_qty  x self.n_frame) bytes into buff

            if len(buff) < (self.read_qty * self.n_frame):
                raise TimeoutError("connection error")

            start_f = 0  # start point of the frames in the buffer

            while start_f < self.read_qty * self.n_frame:  # loop as long we havent reached (self.read_qty  x self.n_frame) bytes

                r = buff[start_f]  # read first byte of first frame in the buffer

                if r == 0x4D:  # if it is a "M" we can start unpacking

                    frame = buff[start_f:start_f + self.read_qty]  # we take one frame
                    start_f += self.read_qty  # we update start_f for the read of the next frame

                    hash = crc8()  # crc8
                    hash.update(frame)  # check if received data is ok

                    if hash.hexdigest() == "00":  # if crc value is 0, then frame is ok.

                        vals = struct.unpack(f, frame[1:-1])  # unpack and put result in array

                        if transpose:
                            for p in range(0, self.n_channels):
                                ret[count][p] = vals[p]  # list array at the end with sz_block x n_ports dimensions
                        else:
                            for p in range(0, self.n_channels):
                                ret[p][count] = vals[p]  # list array at the end with sz_block x n_ports dimensions

                        count += 1  # update count
                        if count >= self.sz_block:  # if count >= sz_block, we are ready and we return all the values
                            return ret

                else:
                    r = self.con.read(1)  # we read one byte
                    buff = buff[1:] + r  # we slide buff and append the new byte at the end, then we try again
"""