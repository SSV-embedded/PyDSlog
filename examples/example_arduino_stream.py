import PyDSlog.stream as stream
import time

p           = "COM11"
brate       = 115200
chan        = ["C1","C2","C3","C4","C5","C6","C7","C8"]
freq        = 100
bl_sz       = 100
signal      = False


x = stream.Arduino_stream(port=p, channels_to_use=chan, frequency=freq,
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