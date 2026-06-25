from celery import Celery
from fastapi import FastAPI

from examples.models import OrderCreate, OrderResult
from queuebridge.celery import register_queuebridge, typed_result

app = FastAPI()
celery_app = Celery(
    "orders",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
register_queuebridge(celery_app)


@celery_app.task(pydantic=True)
def process_order(order: OrderCreate) -> OrderResult:
    return OrderResult(id=order.id, status="processed")


@app.post("/orders")
def enqueue(order: OrderCreate) -> dict[str, str]:
    ar = process_order.delay(order)
    return {"task_id": ar.id}


@app.get("/orders/{task_id}")
def get_result(task_id: str) -> dict[str, object]:
    from celery.result import AsyncResult

    ar = AsyncResult(task_id, app=celery_app)
    result = typed_result(ar, OrderResult).get(timeout=10)
    return result.model_dump()
