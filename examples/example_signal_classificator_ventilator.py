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


