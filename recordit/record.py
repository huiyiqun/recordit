import av

def record(web_video, dump_file):
    input_ = av.open(web_video)
    output = av.open(dump_file, 'w')

    io_map = {}
    # Dump streams info
    for stream in input_.streams:
        print(stream)
        io_map[stream] = output.add_stream(template=stream)

    pkts = 0
    for packet in input_.demux(streams=tuple(input_.streams)):
        if packet.dts is None:
            pass

        packet.stream = io_map[packet.stream]
        print(packet)
        output.mux(packet)
        pkts += 1
        if pkts > 1000:
            break

    output.close()


if __name__ == '__main__':
    record('http://iptv.tsinghua.edu.cn/hls/cctv1hd.m3u8', '/tmp/output.mp4')
