import PyDSlog.stream as stream

x = stream.Arduino_stream(sz_block=100, channels_to_use=["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"],
                                frequency=5, port="COM11", baudrate=115200)

try:
    print("start")
    x.connect()
    x.start()

    for i in range(0, 60):

        r = x.read()
        print(r)


finally:
    x.stop()
    x.disconnect()
    print("stop")