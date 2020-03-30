"""
  ____          ____   ____   _                         ____  ____ __     __
 |  _ \  _   _ |  _ \ / ___| | |  ___    __ _          / ___|/ ___|\ \   / /
 | |_) || | | || | | |\___ \ | | / _ \  / _` |  _____  \___ \\___ \ \ \ / /
 |  __/ | |_| || |_| | ___) || || (_) || (_| | |_____|  ___) |___) | \ V /
 |_|     \__, ||____/ |____/ |_| \___/  \__, |         |____/|____/   \_/
         |___/                          |___/

"""

import PyDSlog.stream.MQTTStream as stream  # import Stream module
import threading
import queue
import os
import sys

class MQTT_csv_saver:

    def __init__(self, channels_to_use, filepath, mqtt_port, mqtt_ip, mqtt_topic="pydslog/0/in/", json_index="payload", filename=None, labeled=False, save_as_signal=False,
                 header=True, custom_header=None, w_mode="a", delimiter=","):


        self.generation_status = {0:"start", 1:"pause", 2:"stop", 3:"error"}
        self.status            = 1                                # always the initial status
        self.error_str         = ""

        self.run_label         = ""                               # Set label to empty string. this are numbers that came over mqtt and represents the machine state
        self.values_count      = 0

        self.sem_1                          = threading.Semaphore()  # semaphore to savely read the mqtt global variables (run_label)
        self.sem_2                          = threading.Semaphore()
        self.sem_3                          = threading.Semaphore()
        self.sem_4                          = threading.Semaphore()


        self.stream_thread_keepalive_flag   = threading.Event()      # this flag keeps the thread_read_stream alive as long end_csv() is not called
        self.start_flag                     = threading.Event()      # this flag control the generation of the csv file depending of the value of "run_cmd"


        self.topic             = mqtt_topic
        self.json_index        = json_index
        self.mqtt_ip           = mqtt_ip
        self.mqtt_port         = mqtt_port

        self.labeled           = labeled
        self.channels_to_use   = channels_to_use                  # store the channels to use in loval variable.

        self.filename          = filename                         # store filepath in local variable
        self.filepath          = filepath                         # the filepath where the files are stored

        self.header            = header                           # add header flag for normal csv
        self.custom_header     = custom_header                    # add custom header in normal csv file
        self.delimiter         = delimiter                        # the delimiter between values
        self.mode              = w_mode                           # file open mode. "a" or "w"
        self.save_as_signal    = save_as_signal                   # save as signal or as normal csv file

        self.stream_values     = queue.Queue(0)                   # queue for storing the stream values. One thread put values and the other read the values. So we dont block
        self.serial_con        = None                             # serial connection. None at the beginning
        self.time_d            = 0                                # variable where we store the time that takes when we are reading the stream values.

        self.thread_read_stream             = threading.Thread(target=self.thread_read_channels, args=())    # thread for reading the stream

        if(save_as_signal):                                          # if save_as_signal is true, then we define the threads for signal csv generation

            self.thread_do_csv = threading.Thread(target=self.thread_do_csv_signal, args=())

        else:                                                        # if not, then we define the threads for normal csv generation

            self.thread_do_csv = threading.Thread(target=self.thread_do_csv_normal, args=())


    def check_if_folder_exist_and_create(self):                       # function that checks if path exist and if not, create it

        if not os.path.exists(self.filepath):                         # create file folder if not exist
            os.makedirs(self.filepath)

    def generate_header(self):                                        # function that generates the header of the csv file. Only when the "save_as_signal" is not True

        header = ""
        if(self.header == True):

            if(self.custom_header is None):

                header += self.delimiter.join(self.channels_to_use)

                if(self.labeled):
                    header += self.delimiter + "label" + "\n"
                else:
                    header += "\n"
            else:

                header = self.custom_header + "\n"

        return header


    def format_csv(self, v):                                # Function that formats the csv file when "save_as_signal" is False.

        csv = ""
        for d in range(0, len(v)):

            self.sem_1.acquire()
            local_label = self.run_label
            self.sem_1.release()

            line = ""
            row = v[d]
            line += self.delimiter.join(str(x) for x in row)

            if(self.labeled):
                line += self.delimiter + local_label

            csv += line + "\n"

        return csv                                          # return csv string


    def thread_read_channels(self):

        try:

            mqtt_stream = stream.MQTT_stream(self.topic, self.mqtt_ip, self.mqtt_port, self.channels_to_use, self.json_index)

            self.start_flag.wait()

            mqtt_stream.start()

            while(self.stream_thread_keepalive_flag.is_set()):

                if(self.start_flag.is_set()):

                    if(mqtt_stream.values_waiting_in_MQTT_stream()):
                        v = mqtt_stream.read(transpose=(not self.save_as_signal))
                        self.stream_values.put(v)

                        self.sem_3.acquire()
                        self.values_count += 1
                        self.sem_3.release()

                else:
                    if(mqtt_stream.values_waiting_in_MQTT_stream()):
                        r = mqtt_stream.read(transpose=(not self.save_as_signal))       # read so the stream buffer is empty

            mqtt_stream.stop()

        except Exception as err:

            self.sem_2.acquire()
            self.status  = 3
            self.sem_2.release()

            self.sem_4.acquire()
            self.error_str = str(err)
            self.sem_4.release()
            raise err

    def thread_do_csv_normal(self):                         # thread that generates a normal labeled csv file.

        self.check_if_folder_exist_and_create()

        try:

            if(self.filename == ""):
                raise ValueError("no filename defined")

            f = open(self.filepath + self.filename, self.mode)  # open files
            if(os.stat(self.filepath + self.filename).st_size == 0): # if file has nothing, then write header
                header = self.generate_header()
                f.write(header)

            while(self.stream_thread_keepalive_flag.is_set()):      # keep alive as long "stream_thread_keepalive_flag" is set

                if(self.stream_values.empty() == False):            # if the "stream_values" is not empty

                    try:
                        v = self.stream_values.get(block=False)     # read queue  / non blocking
                    except queue.Empty:
                        pass
                    else:
                        csv = self.format_csv(v)                    # format stream values to csv string

                        f.write(csv)                                # write csv

            f.close()                                               # close file

        except Exception as err:

            self.sem_2.acquire()
            self.status  = 3
            self.sem_2.release()

            self.sem_4.acquire()
            self.error_str = str(err)
            self.sem_4.release()


    def thread_do_csv_signal(self):                                 # thread that generate a labeled signal csv file.

        self.check_if_folder_exist_and_create()

        try:

            f_x = []
            for c in (self.channels_to_use):                        # open file for every element in "channels_to_use"
                f_x.append(open(self.filepath + "x_" + c + "_" + ".csv", self.mode))

            if(self.labeled):
                f_y = open(self.filepath + "y_" +".csv", self.mode) # open label file

            while(self.stream_thread_keepalive_flag.is_set()):      # keep alive as long "stream_thread_keepalive_flag" is set

                if(self.stream_values.empty() == False):            # if the "stream_values" is not empty

                    try:
                        v = self.stream_values.get(block=False)     # read queue  / non blocking
                    except queue.Empty:
                        pass
                    else:
                        self.sem_1.acquire()
                        local_label  = self.run_label                # look for actual "run_label"
                        self.sem_1.release()

                        if(self.labeled):
                            f_y.write(str(local_label) + "\n")        # write label in label file

                        for n in range(0, len(v)):                          # for every channel or dimension in the returned list
                            line = ""
                            row = v[n]                                       # select one channel. --> (v is a n-dimensional-list with every dimension a channel) <--
                            line += self.delimiter.join(str(x) for x in row) # signal to string with dlimiter
                            f_x[n].write(line + "\n")                        # write complete signal in row of the csv file


            if(self.labeled):
                f_y.close()

            for f in f_x:                                              # close files
                f.close()

        except Exception as err:

            self.sem_2.acquire()
            self.status  = 3
            self.sem_2.release()

            self.sem_4.acquire()
            self.error_str = str(err)
            self.sem_4.release()

            raise err


    def get_status(self, status_text=True):

        self.sem_1.acquire()
        local_label     = self.run_label
        self.sem_1.release()

        self.sem_2.acquire()
        local_status    = self.status
        self.sem_2.release()

        self.sem_3.acquire()
        local_count     = self.values_count
        self.sem_3.release()

        self.sem_4.acquire()
        local_error     = self.error_str
        self.sem_4.release()

        if(status_text):
            status = self.generation_status[local_status]
        else:
            status = local_status


        return {"label":local_label, "count":local_count, "status":status, "err_info": local_error}


    def set_label(self, label):

        self.sem_1.acquire()
        self.run_label = label
        self.sem_1.release()


    def start(self):          # function that start the threads and set the flags for start the generation of the csv file

        self.sem_2.acquire()
        self.status = 0
        self.sem_2.release()
        self.start_flag.set()
        self.stream_thread_keepalive_flag.set()
        if (not self.thread_read_stream.is_alive()):
            self.thread_read_stream.start()
        if (not self.thread_do_csv.is_alive()):
            self.thread_do_csv.start()


    def pause(self):

        self.start_flag.clear()
        self.sem_2.acquire()
        self.status = 1
        self.sem_2.release()


    def stop(self):

        self.start_flag.clear()
        self.stream_thread_keepalive_flag.clear()
        self.sem_2.acquire()
        self.status = 2
        self.sem_2.release()
        self.thread_do_csv.join()
        self.thread_read_stream.join()
