import av

from datetime import datetime
from celery import Celery
from celery.contrib.abortable import AbortableTask
from celery.utils.log import get_task_logger

# TODO: configurable
app = Celery(__name__,
             backend='redis://localhost/',
             broker='redis://localhost/')
logger = get_task_logger(__name__)


@app.task(bind=True, base=AbortableTask)
def record(self, web_video, dump_file, until=None):
    input_ = av.open(web_video)
    output = av.open(dump_file, 'w')

    io_map = {}
    # copy meta info
    for stream in input_.streams:
        print(stream)
        io_map[stream] = output.add_stream(template=stream)

    # remux packets
    for packet in input_.demux(streams=tuple(input_.streams)):
        if packet.dts is None:
            continue

        packet.stream = io_map[packet.stream]
        output.mux(packet)

        # time out
        if until is not None and datetime.utcnow() > until:
            break

        # aborted
        if self.is_aborted():
            break

    logger.info(f'{web_video} is dumped to {dump_file}')
    output.close()
