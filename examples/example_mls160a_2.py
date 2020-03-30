import PyDSlog.stream as stream

x = stream.MLS160A_stream(sz_block=500, channels_to_use=["ACCX","ACCY","ACCZ","GYRX","GYRY","GYRZ"],
                                      frequency=500, port="COM15", baudrate=115200, n_frame=100)

try:
    print("start")
    x.connect()
    x.start()

    for i in range(0, 60):

        r = x.read()


finally:
    x.stop()
    x.disconnect()
    print("stop")