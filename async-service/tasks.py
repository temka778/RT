import pika
import json

RABBIT_URL = "amqp://guest:guest@rabbitmq/"

def send_task_to_queue(task_id, equipment_id, parameters):
    connection = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
    channel = connection.channel()
    queue_name = "task_dispatcher"

    channel.queue_declare(queue=queue_name, durable=True)
    message = json.dumps({
        "task_id": task_id,
        "equipment_id": equipment_id,
        "parameters": parameters
    })
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
