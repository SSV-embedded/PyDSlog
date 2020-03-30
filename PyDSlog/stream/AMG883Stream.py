"""
  ____          ____   ____   _                         ____  ____ __     __ 
 |  _ \  _   _ |  _ \ / ___| | |  ___    __ _          / ___|/ ___|\ \   / / 
 | |_) || | | || | | |\___ \ | | / _ \  / _` |  _____  \___ \\___ \ \ \ / /  
 |  __/ | |_| || |_| | ___) || || (_) || (_| | |_____|  ___) |___) | \ V / 
 |_|     \__, ||____/ |____/ |_| \___/  \__, |         |____/|____/   \_/ 
         |___/                          |___/                     

"""
from PyDSlog.crc8 import crc8
import serial
import struct
import time

class AMG883_stream:

    def __init__(self, frequency, port, baudrate):

        self.port = port

        try:
            self.sz_block = 8
            self.baudrate = int(baudrate)
            self.n_frame = 8
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


        self.read_qty = 2 + (8 * 2)      # Calculate expected bytes to read

        self.write_timeout = 1
        self.read_timeout = ((self.read_qty * self.n_frame)/self.frequency) + 1


    def connect(self):

        try:
            self.con = serial.Serial(self.port, self.baudrate, write_timeout=self.write_timeout, timeout=self.read_timeout)
        except (IOError, serial.SerialException) as e1:
            raise e1
        except ValueError as e2:
            raise e2


    def disconnect(self):

        self.con.close()


    def start(self):

        n_chan = 8
        start_flag = "A"
        chan_in   =  255

        f_upper = (self.frequency >> 8) & 0xff   # upper
        f_lower = self.frequency & 0xff          # lower

        f_max = 11520/((2*n_chan) + 3)     # Calculate max frequency

        if f_max < self.frequency:
            raise NameError("Frequency is too high for selected quantity of channels")  # if the selected frequency is higher to f_max,
                                                                                        # then print alert

        arr = [ord(start_flag), chan_in, f_lower, f_upper]  # put everything in one list

        b_arr = bytearray(arr)              # bytearray from list

        hash = crc8()                       # crc8
        hash.update(b_arr)                  # crc with buff
        crc_val = hash.digest()             # read crc value
        b_arr = b_arr + crc_val             # add crc_val to the end of the bytearray

        time.sleep(2)                       # Arduino need some time because it reset after a new connection

        try:
            self.con.write(b_arr)            # write buff with streaming settings
        except serial.SerialTimeoutException as e:
            raise e


    def stop(self):

        try:

            for i in range(0,512):                               # send 512 times "z" to stop the streaming mode
                self.con.write(b"\x5A")

        except serial.SerialTimeoutException as e:
            raise e


    def read(self, transpose=False):

        f = ">" + str(8) + "h"                     # h for the format integer. see python struct formats
        #f = str(8) + "H"  # h for the format integer. see python struct formats

        ret = [[0 for j in range(8)] for i in range(8)] # use list

        count = 0                                               # counter. If this counter has the value of sz_block,
                                                                # then we are ready and return N-array with values

        while 1:                                                # loop

            buff = self.con.read(self.read_qty * self.n_frame)  # read (self.read_qty  x self.n_frame) bytes into buff

            if len(buff) < (self.read_qty * self.n_frame):
                raise TimeoutError("connection error")

            start_f = 0                                        # start point of the frames in the buffer

            while start_f < self.read_qty  * self.n_frame:     # loop as long we havent reached (self.read_qty  x self.n_frame) bytes

                r = buff[start_f]                              # read first byte of first frame in the buffer

                if r == 0x4D:                                  # if it is a "M" we can start unpacking

                    frame = buff[start_f:start_f + self.read_qty ]    # we take one frame
                    start_f += self.read_qty                          # we update start_f for the read of the next frame

                    hash = crc8()                               # crc8
                    hash.update(frame)                          # check if received data is ok

                    if hash.hexdigest() == "00":                # if crc value is 0, then frame is ok.

                        fr = frame[1:-1]
                        print(frame)
                        for i in range(0, 8):
                            z = int((fr[i*2] & 0xf0)/16)
                        print(z)

                        values = []
                        for i in range(1, len(fr)+1):
                            if i%2:
                                values.append(fr[i-1] & 0x0f)
                            else:
                                values.append(fr[i-1])

                        values = bytearray(values)

                        vals = struct.unpack(f, values)     # unpack and put result in array
                        #print(vals)

                        for p in range(0, 8):
                            ret[z][p] = vals[p]  # list array at the end with sz_block x n_ports dimensions

                        count += 1                                # update count
                        if count >= 8:                # if count >= sz_block, we are ready and we return all the values
                            return ret

                else:
                    print("error")
                    r = self.con.read(1)                          # we read one byte
                    buff = buff[1:] + r                           # we slide buff and append the new byte at the end, then we try again
