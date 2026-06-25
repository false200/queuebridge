from arq.connections import RedisSettings
from pydantic import validate_call

from examples.models import OrderCreate, OrderResult
from queuebridge.arq import get_serializer_pair, qb_task

serialize, deserialize = get_serializer_pair()


@qb_task
@validate_call
async def process_order(ctx: dict, order: OrderCreate) -> OrderResult:
    return OrderResult(id=order.id, status="ok")


class WorkerSettings:
    functions = [process_order]
    redis_settings = RedisSettings()
    job_serializer = serialize
    job_deserializer = deserialize
