import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import pika
import json
import requests
import time
from db import update_task_status

RABBIT_URL = "amqp://guest:guest@rabbitmq/" # для Docker Compose
# RABBIT_URL = "amqp://guest:guest@localhost/" # без Docker Compose
QUEUE_NAME = "task_dispatcher"
RESULT_QUEUE = "task_results"

def connect_to_rabbitmq_with_retry(retries=10, delay=3):
    for attempt in range(retries):
        try:
            print(f"[*] Попытка подключения к RabbitMQ ({attempt + 1}/{retries})...")
            connection = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
            print("[✓] Успешно подключено к RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[!] Не удалось подключиться к RabbitMQ: {e}")
            time.sleep(delay)
    raise Exception("❌ Не удалось подключиться к RabbitMQ после нескольких попыток")

def publish_result(task_id, status):
    connection = connect_to_rabbitmq_with_retry()
    channel = connection.channel()
    channel.queue_declare(queue=RESULT_QUEUE, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=RESULT_QUEUE,
        body=json.dumps({"task_id": task_id, "status": status}),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

def callback(ch, method, properties, body):
    print("[*] Получена задача из очереди")
    try:
        data = json.loads(body)
        task_id = data['task_id']
        equipment_id = data['equipment_id']
        parameters = data['parameters']

        print(f"[*] Отправляем запрос в сервис A для task {task_id}")
        for attempt in range(3):
            try:
                response = requests.post(
                  #  f"https://localhost:5001/api/v1/equipment/cpe/{equipment_id}", # без Docker Compose
                    f"https://equipment-configurator:5001/api/v1/equipment/cpe/{equipment_id}", # для Docker Compose
                    json={"timeoutInSeconds": 14, "parameters": parameters},
                    timeout=62,
                    verify=False
                )
                if response.status_code == 200:
                    update_task_status(task_id, "completed")
                    publish_result(task_id, "completed")
                    print(f"[✓] Task {task_id} успешно выполнена")
                else:
                    update_task_status(task_id, "failed")
                    publish_result(task_id, "failed")
                    print(f"[x] Ошибка при выполнении task {task_id}: {response.status_code} — {response.text}")
                break
            except requests.Timeout:
                print(f"[!] Таймаут при вызове сервиса A для task {task_id}, попытка {attempt + 1}")
                if attempt == 2:
                    update_task_status(task_id, "failed")
                    publish_result(task_id, "failed")
                    print(f"[x] Не удалось выполнить task {task_id} после 3 попыток")
            except Exception as e:
                print(f"[!] Ошибка при вызове сервиса A: {str(e)}")
                if attempt == 2:
                    update_task_status(task_id, "failed")
                    publish_result(task_id, "failed")
                    print(f"[x] Не удалось выполнить task {task_id} после 3 попыток")

    except Exception as e:
        print(f"[!] Исключение при обработке задачи: {str(e)}")
        update_task_status(task_id, "failed")
        publish_result(task_id, "failed")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print("[*] Воркер запущен, ожидание задач...")
    connection = connect_to_rabbitmq_with_retry()
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[!] Воркер остановлен вручную")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
