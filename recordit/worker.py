import av

from datetime import datetime, timedelta
from sqlalchemy import event
from celery import Celery
from celery.contrib.abortable import AbortableTask
from celery.utils.log import get_task_logger

from .model import Recording

# TODO: configurable
app = Celery(__name__,
             backend='redis://localhost/',
             broker='redis://localhost/')

app.conf.update(
    accept_content=['pickle', 'json'],
)

logger = get_task_logger(__name__)


@app.task(bind=True, base=AbortableTask, acks_late=True, serializer='pickle')
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


@event.listens_for(Recording, 'before_insert')
def add_task(mapper, connection, target):
    start_time = target.next_start_time()

    kwargs = {
        'web_video': target.url,
        'dump_file': f'{target.name}-{start_time}.mp4',
    }
    if target.duration is not None:
        kwargs['until'] = start_time + timedelta(seconds=target.duration)

    result = record.apply_async(kwargs=kwargs, eta=start_time)
    target._task = result.id
