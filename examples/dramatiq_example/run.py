import dramatiq
from dramatiq.brokers.redis import RedisBroker
from pydantic import validate_call

from examples.models import OrderCreate
from queuebridge.dramatiq import register_queuebridge

broker = RedisBroker()
dramatiq.set_broker(broker)
register_queuebridge()


@dramatiq.actor
@validate_call
def process(order: OrderCreate) -> None:
    print(order)


if __name__ == "__main__":
    process.send(OrderCreate(id=1, sku="X"))
