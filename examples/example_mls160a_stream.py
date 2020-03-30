import PyDSlog.stream as stream
import time

p           = "COM3"
brate       = 115200
chan        = ["ACCX","ACCY","ACCZ"]
freq        = 1
bl_sz       = 10
signal      = False


x = stream.MLS160A_stream(port=p, channels_to_use=chan, frequency=freq,
                          sz_block=bl_sz, baudrate=brate)

x.connect()
x.start()
t0a = time.time()
v = x.read(transpose=True)
t0b = time.time()
x.stop()
x.disconnect()

t0 = t0b-t0a
print(t0)

print(v)