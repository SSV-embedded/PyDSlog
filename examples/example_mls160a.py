import PyDSlog.stream as stream
import matplotlib.pyplot as plt
import numpy as np

titles = ["Acc X", "Acc Y", "Acc Z", "Ang X", "Ang Y", "Ang Z"]
#chan = ["ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ"]

chan = ["ACCX","ACCY","ACCZ"]



x = stream.MLS160A_stream(sz_block=600, channels_to_use=chan,
                                      frequency=1200, port="COM16", baudrate=115200, n_frame=100)


print("start")
x.connect()
x.start()


r = x.read(transpose=False)

r = np.array(r)

x.stop()
x.disconnect()
print("stop")



fig, ax = plt.subplots(nrows=len(chan), ncols=1,figsize=(12, 6))

titles = ["Acc X", "Acc Y", "Acc Z", "Ang X", "Ang Y", "Ang Z"]

for c in range(r.shape[0]):
    ax[c].plot(r[c,:], linestyle='-')
    ax[c].set_title(titles[c], fontsize=16)
    ax[c].set_xlabel('Time', fontsize=10)
    ax[c].set_ylabel('Amplitude', fontsize=10)

fig.tight_layout()
plt.show()