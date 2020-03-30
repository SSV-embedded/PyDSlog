import PyDSlog.stream as stream

x = stream.IO5640_stream(sz_block=100, channels_to_use=["AI4U", "AI3U", "AI2U", "AI1U", "AI1I", "AI2I"],
                                frequency=500, port="COM15", baudrate=115200)

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