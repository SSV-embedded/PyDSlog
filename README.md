![alt text](https://github.com/SSV-embedded/PyDSlog/blob/master/images/io5640-ds_plus_pydslog.jpg "PyDSlog data streaming library")

# PyDSlog

This app is installed by default on the RMG/941. It allows to read the sensor values coming from the serial RS485 interface 
or via MQTT and stores them in CSV files.

PyDSlog claims to make the data acquisition for machine learning and AI applications in the RMG/941 fast and easy.

### Access to stream

To use the stream it is necessary to initialize the class with the desired frequency, the desired channels, the serial 
port and the size of the block to be read.

For the MLS/160A:
```
x = PyDSlog.stream.MLS160A_stream(sz_block=500, channels_to_use=["ACCX", "ACCY", "ACCZ", "GYRX", "GYRY", "GYRZ"],
         frequency=500, port="COM15", baudrate=115200, n_frame=100)
```
and for the IO5640-DS:
```
x = PyDSlog.stream.IO5640_stream(sz_block=100, channels_to_use=["AI4U", "AI3U", "AI2U", "AI1U", "AI1I", "AI2I"], 
        frequency=500, port="COM15", baudrate=115200)
```
Where:

* sz_block: is the size of the block to be read at once when the stream is read.
* channels_to_use: are the channels to use. Possible are ```["ACCX", "ACCY", "ACCZ", "GYRX", "GYRY", "GYRZ"]``` for 
the MLS/160A and ```["AI4U", "AI3U", "AI2U", "AI1U", "AI1I", "AI2I"]``` for the IO5640-DS.
* frequency: is the desired frequency and ```port``` is the serial port. the baudrate is fixed at 115200 and can not 
be changed.

To access the stream directly it is necessary to connect the sensor to the serial port. The ```connect()``` method is used 
for this purpose. To start the stream the ```start()``` method is used. After calling the ```start()``` function, the sensor will 
start sending the values of the selected channels with the desired frequency. To read the values, use the ```read(transpose=False)``` method. 
Finally to stop the stream you use the ```stop()``` method and to release the serial port ```disconnect()```.

As an example, using MLS/160A:


```
# import PyDSlog
import PyDSlog.stream as stream

# size of the block to read is 500
# the channels that will be streamed are ["ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ"]
# a frequency of 500 Hz
# sensor is connected to port COM15
# the baudrate is fixed at 115200 and can not be changed.
x = stream.MLS160A_stream(sz_block=500, channels_to_use=["ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ"],
                                      frequency=500, port="COM15", baudrate=115200, n_frame=100)

try:

    # connect
    x.connect()

    # start
    x.start()

    # read stream. if you want to to transpose the values use transpose = True.
    r = x.read(transpose=False)


finally:
    
    # stop
    x.stop()
    # disconnect from port
    x.disconnect()


```
### Generate CSV file from sensor values

PyDSlog was developed for the purpose of generating csv files to be used for training Machine Learning algorithms.

The following classes are available for this purpose:


For the MLS/160A:
```
x = PyDSlog.csv.MLS160A_csv_saver(port, channels_to_use, frequency, block_size, filepath, filename=None, labeled=False, save_as_signal=False,
                 header=True, custom_header=None, add_tmp=None, date_format="%d/%m/%Y,%H:%M:%S", baudrate=115200, w_mode="a", delimiter=",")

```

and for the IO5640-DS:
```
x = PyDSlog.csv.IO5640_csv_saver(port, channels_to_use, frequency, block_size, filepath, filename=None, labeled=False, save_as_signal=False,
                 header=True, custom_header=None, add_tmp=None, date_format="%d/%m/%Y,%H:%M:%S", baudrate=115200, w_mode="a", delimiter=",")

```

Where:

```sz_block``` is the size of the block to be read at once when the stream is read.
```channels_to_use``` are the channels to use. Possible are ```["ACCX", "ACCY", "ACCZ", "GYRX", "GYRY", "GYRZ"]``` for 
the MLS/160A and ```["AI4U", "AI3U", "AI2U", "AI1U", "AI1I", "AI2I"]``` for the IO5640-DS.
```frequency``` is the desired frequency and ```port``` is the serial port. the baudrate is fixed at 115200 and can not 
be changed.

* Labeled: default False. boolean.
If the sensor values have to be labelled (in order to be used with Supervised Learning), it is necessary to use ```labeled=True```.
* filepath: default None. string pointing to the location of the csv file.
filename: default None. string with name of file.
* save_as_signal: default False. boolean.
If the values have to be interpreted as signals, it is necessary to use ```save_as_signal=True```. This makes it possible to use an FFT function later. A separate csv file is generated for each channel. The values that represent a signal are separated by commas. A newline character separates the signals from each other. Each signal has a length of sz_block values.
* header: default True. boolean.
If true, the name of the channel is used as the header
* custom_header: default None. string
In case a different header than the name of the channels is needed.
* add_tmp: default None. also possible: date, us or ms.
In case you want to use a timestamp. for ```add_tmp="date"``` the format in ```date_format``` is used.
* date_format: default ```"%d/%m/%Y,%H:%M:%S"```
The format for the date used. only necessary if ```add_tmp="date"``` 
* delimiter: ","
The separator character used.

Once the class to generate the CSV file is initialized it is possible to use the ```start()``` method to start saving the 
sensor values into the CSV file. The ```pause()``` method can be used to pause. This method stops the sensor stream but does
 not close the CSV file or release the serial port. To reactivate the stream and save more values in the file, the ```start()```
  method can be used again. Finally, the ```stop()``` method is used to end the recording.

If the values are labeled it is possible to use the ```set_label(label)``` method to configure the label to be used. The 
```label``` parameter is a number that represents the label with which the values are stored in the file.

As an example, using MLS/160A:

```
# import libraries
import PyDSlog.csv as csv
import time


# initialize 
x = csv.MLS160A_csv_saver(port="COM3", channels_to_use=["ACCX","ACCY","ACCZ"], frequency=500,
                          block_size=500, filepath="test/", filename="file.csv",
                          labeled=False, save_as_signal=False, header=True,
                          add_tmp="ms", baudrate=115200, w_mode="a")

# start
x.start_csv()

# wait..
time.sleep(3)

#pause
x.pause_csv()

#wait again
time.sleep(3)

# restart
x.start_csv()

# wait again..
time.sleep(3)

# terminate
x.stop_csv()

```

The output will be something like:

![alt text](https://github.com/SSV-embedded/PyDSlog/blob/master/images/csv.jpg "CSV demo file")


### Do FFT

PyDSlog has a small class included to help transform the signals into the frequency spectrum.

*Dependencies: you have to install numpy and scipy before you can use this module*

```
import PyDSlog.transform as fft
import PyDSlog.stream as stream
import matplotlib.pyplot as plt
import numpy as np

chan = ["ACCX","ACCY","ACCZ"]
serial_port = "COM6"
frequency = 400
size_signal = 400
period = 1.0/frequency

# initialize
transform = fft.FFTGenerator(period, size_signal, frequency)
x = stream.MLS160A_stream(sz_block=size_signal, channels_to_use=chan,
                                      frequency=frequency, port=serial_port, baudrate=115200)

# read values as signal
sensor_values = x.read(transpose=False)
sensor_values = np.array(sensor_values)

# transform
ffts_val = transform.doFFT(sensor_values, delete_offset=True)  
# where ffts_val[0,c,:,0] are frequencies and ffts_val[0,c,:,1] are the amplitudes

# plot
plt.plot(ffts_val[0,c,:,0], ffts_val[0,c,:,1], linestyle='-', label="FFT")
plt.show()
 
```

### PyDSlog simple signal classifier

PyDSlog includes a simple signal classifier. This classifier consists in forming groups where a master vector is stored 
according to its correlation. During each learning cycle the correlation of the new vector with the master vector of each 
group is compared.  It is assumed that the master vector in the group with the highest correlation to the new vector is the 
group to which the new vector belongs. Once the group is found, a new master vector is calculated and stored in the group 
to be used in future operations.

Once the learning process has been completed, it is possible to predict which group a new vector belongs to by calculating 
the average distance to the master vector from the group with the highest correlation.

*Dependencies: you have to install numpy and scipy before you can use this module. For advanced functionality it is also 
recommended to install scikit-learn*

The class:
```
PyDSlog.classificator.SignalClassificator(min_pears_correlation=0.7, max_subgroups=5, outliers=False)
```
where:

* min_pears_correlation: Default is 0.7. float.
is the minimum pearson correlation to be used to group a new vector to a group. 
* max_subgroups: Default is 5. integer.
is the maximum quantity of groups generated while learning.
* outliers: Default False. Boolean.
If the average distance found when predicting a class for a new vector is lower than the tolerance (see ```predict(signals, tolerance)```), then return -1 
as class indicating that it is an unknown class or an anomaly

To train the algorithm it is necessary to use the ```fit( x_train, y_train)``` method. Where ```x_train``` are the signals 
and ```y_train``` are the labels.

To make a prediction it is necessary to use the ```predict(signals, tolerance)``` method. Where signals is the vector to be 
classified and the tolerance is a number that indicates the tolerance to be used. If the average distance (or difference) 
of the new vector from the master vector within each group is greater than the tolerance, then the vector belongs to an 
unknown class or is an anomaly (-1).

As an example:
```
import PyDSlog.classificator as classificator
import PyDSlog.transform as transform
import pandas as pd
import numpy as np


##################   STREAM DATA PARAMETERS    #################

N = 5000
fs = 500
T = 1 / fs

PREFIX = "1478217877058"

X_FILES = [PREFIX+"_x_ACCX_.csv",PREFIX+"_x_ACCY_.csv",PREFIX+"_x_ACCZ_.csv",
           PREFIX+"_x_GYRX_.csv",PREFIX+"_x_GYRY_.csv",PREFIX+"_x_GYRZ_.csv"]

Y_FILE = PREFIX+"_y_.csv"


def read_signals(name):
    r = pd.read_csv(name, header=None, index_col=None)
    return r


signals = []
for file in X_FILES:
    s = np.array(read_signals("../test/test/"+file))
    signals.append(s)
signals = np.transpose(np.array(signals), (1, 0, 2))

labels = np.array(pd.read_csv("../test/test/"+Y_FILE, header=None, index_col=None))
labels = np.squeeze(labels)

t = transform.FFTGenerator(T, N, fs)
v_ffts = t.doFFT(signals, delete_offset=True)
print(v_ffts.shape)

##################   TRAIN TEST SPLIT    #################

from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(v_ffts[:,:,:,1], labels, test_size=0.4)

cls = classificator.SignalClassificator()
cls.fit(x_train, y_train)
y_pred = cls.predict(x_test, 4.5, verbose=True)

from sklearn.metrics import classification_report

print(classification_report(y_test, y_pred))
```
