"""
  ____          ____   ____   _                         ____  ____ __     __
 |  _ \  _   _ |  _ \ / ___| | |  ___    __ _          / ___|/ ___|\ \   / /
 | |_) || | | || | | |\___ \ | | / _ \  / _` |  _____  \___ \\___ \ \ \ / /
 |  __/ | |_| || |_| | ___) || || (_) || (_| | |_____|  ___) |___) | \ V /
 |_|     \__, ||____/ |____/ |_| \___/  \__, |         |____/|____/   \_/
         |___/                          |___/

"""
from __future__ import division, print_function
import scipy.signal as signal
from scipy.fftpack import fft
import pandas as pd
import numpy as np
import os

__author__ = "FBU, www.ssv-embedded.de"
__version__ = "0.0.1"

class FFTGenerator:

    def __init__(self, T, N, fs):

        self.period = T
        self.len = N
        self.frequency = fs

    def doFFT(self, values, delete_offset=True, to_file=False, path=None, filenames=None):

        # expand dimension to 3. So we can use this function with one or with many signals
        for n in range(len(values.shape), 3):
            values = np.expand_dims(values, axis=0)

        _ffts = []
        for n in range(0, values.shape[0]):

            _c = []
            for c in range(0, values.shape[1]):

                v = values[n,c,:]

                if delete_offset:
                    v = signal.detrend(v, type == 'constant')

                freq_v = np.linspace(0.0, 1.0 / (2.0 * self.period), self.len // 2)
                fft_v_ = fft(v)
                fft_v = 2.0 / self.len * np.abs(fft_v_[0:self.len // 2])

                if to_file:

                    if path == None:
                        raise TypeError("path is None")

                    if filenames == None:
                        raise TypeError("filename is None")

                    if not os.path.exists(path):  # create file folder if not exist
                        os.makedirs(path)

                    fft_v = pd.DataFrame(data=fft_v).T
                    fft_v.to_csv(path+"ffty"+filenames[c], index=False, header=False, mode="a")

                    freq_v = pd.DataFrame(data=freq_v).T
                    freq_v.to_csv(path+"fftx"+filenames[c], index=False, header=False, mode="a")

                else:

                    xy_v = np.vstack((freq_v, fft_v)).T
                    _c.append(xy_v)
            _ffts.append(_c)

        if to_file is False:
            return np.array(_ffts)


    def _read_signals(self, name):
        r = pd.read_csv(name, header=None, index_col=None)
        return r


    def FFTsread(self, filenames):

        y = []
        for file in filenames:
            s = np.array(self._read_signals("ffty"+file))
            y.append(s)
        y = np.transpose(np.array(y), (1, 0, 2))

        x = []
        for file in filenames:
            s = np.array(self._read_signals("fftx"+file))
            x.append(s)
        x = np.transpose(np.array(x), (1, 0, 2))

        ncxy = np.stack((x,y), axis=3)

        return ncxy