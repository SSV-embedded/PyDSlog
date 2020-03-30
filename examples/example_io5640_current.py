import PyDSlog.classificator as classificator
import pandas as pd
import numpy as np
from scipy import signal
from scipy.fftpack import fft

##################   STREAM DATA PARAMETERS    #################

N = 400
f_s = 400
T = 1 / f_s

PREFIX = "1573636300455"

X_FILES = [PREFIX+"_x_AI1U_.csv"]

Y_FILE = PREFIX+"_y_.csv"

##################   DELETE OFFSET    #################

def delete_offset(sig):
    sig = signal.detrend(sig,type == 'constant')
    return sig

##################   FFT    #################


def get_fft_values(y_values, T, N, f_s):
    f_values = np.linspace(0.0, 1.0/(2.0*T), N//2)
    fft_values_ = fft(y_values)
    fft_values = 2.0/N * np.abs(fft_values_[0:N//2])
    return f_values, fft_values

##################   GENERATE FFTS    #################

def do_ffts(signals):
    s = []
    for no in range(0, signals.shape[0]):
        c = []
        for co in range(0,signals.shape[1]):
            sig = signals[no,co,:]
            sig = delete_offset(sig)
            freq_values, amp_values = get_fft_values(sig, T, N, f_s)
            xy_values = np.vstack((freq_values, amp_values)).T
            c.append(xy_values)
        s.append(c)
    return np.array(s)

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


signals_ffts = do_ffts(signals)
signals_ffts = signals_ffts[:,:,:,1]

print(signals_ffts.shape)

"""
import matplotlib.pyplot as plt

plt.figure(1,figsize=(20,5))
plt.plot(signals[10,0,:])
plt.plot(signals[150,0,:])
plt.plot(signals[240,0,:])
plt.show()
"""

##################   TRAIN TEST SPLIT    #################

from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(signals_ffts, labels, test_size=0.4)

clf = classificator.SignalClassificator("medium_difference")
clf.fit(x_train, y_train, verbose=True)
y_pred = clf.predict(x_test, 11, verbose=False)

from sklearn.metrics import classification_report

print(classification_report(y_test, y_pred))

"""
plt.figure(1,figsize=(20,5))
plt.plot(clf.master_dict["0"][0,:], color="yellow")
plt.plot(clf.master_dict["1"][0,:], color="green")
plt.plot(clf.master_dict["2"][0,:], color="red")
plt.show()
"""