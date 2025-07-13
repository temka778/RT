# Сервис конфигурации оборудования

Этот проект реализует асинхронный сервис конфигурации оборудования в соответствии с предоставленным тестовым заданием. Он состоит из двух сервисов (A и B), воркера для обработки задач и брокера сообщений RabbitMQ.

## Требования
- Docker и Docker Compose
- Ansible (для автоматизированного развертывания)
- OpenSSL (для генерации SSL-сертификатов)

## Структура проекта
- `equipment-configurator/` — Сервис A (заглушка для конфигурации оборудования).
- `async-service/` — Сервис B (фронтенд для асинхронной конфигурации) и воркер.
- `docs/` — Диаграмма архитектуры.
- `ansible/` — Playbook Ansible для развертывания.
- `docker-compose.yml` — Конфигурация Docker Compose.

## Установка и запуск

### 1. Генерация SSL-сертификатов
Если в папках `equipment-configurator/cert/` и `async-service/cert/` отсутствуют файлы `cert.pem` и `key.pem`, сгенерируйте их:

```bash
mkdir -p equipment-configurator/cert async-service/cert
openssl req -x509 -newkey rsa:4096 -nodes -out equipment-configurator/cert/cert.pem -keyout equipment-configurator/cert/key.pem -days 365 -subj "/CN=localhost"
openssl req -x509 -newkey rsa:4096 -nodes -out async-service/cert/cert.pem -keyout async-service/cert/key.pem -days 365 -subj "/CN=localhost"
```

### 2. Создание директории для базы данных
Создайте директорию для базы данных SQLite:

```bash
mkdir -p async-service/data
```

### 3. Запуск с помощью Docker Compose
```bash
docker-compose up -d
```

### 4. Запуск с помощью Ansible
Альтернативно, используйте playbook Ansible:

```bash
ansible-playbook ansible/deploy.yml
```

### 5. Доступ к сервисам
- **Сервис A**: `https://localhost:5001/api/v1/equipment/cpe/{id}`
- **Сервис B**: 
  - `https://localhost:5002/api/v1/equipment/cpe/{id}` (POST)
  - `https://localhost:5002/api/v1/equipment/cpe/{id}/task/{task_id}` (GET)
- **Интерфейс управления RabbitMQ**: `http://localhost:15672` (логин: guest, пароль: guest)

### 6. Запуск тестов
Запустите интеграционные тесты для каждого сервиса:

```bash
cd equipment-configurator
pytest tests/test_integration.py --disable-warnings
cd ../async-service
pytest tests/test_integration.py --disable-warnings
```

## Архитектура
Диаграмма взаимодействия сервисов находится в файле `docs/architecture.puml`. Для визуализации используйте PlantUML:

```bash
docker run -v $(pwd)/docs:/docs plantuml /docs/architecture.puml
```

## API-эндпоинты
### Сервис A
- **POST /api/v1/equipment/cpe/{id}**
  - Запрос: `{ "timeoutInSeconds": 14, "parameters": { "username": "admin", "password": "admin", "vlan": 534, "interfaces": [1, 2, 3, 4] } }`
  - Ответ: `{ "code": 200, "message": "success" }` (через 60 секунд)

### Сервис B
- **POST /api/v1/equipment/cpe/{id}**
  - Запрос: Аналогичен сервису A
  - Ответ: `{ "code": 200, "taskId": "<uuid>" }`
- **GET /api/v1/equipment/cpe/{id}/task/{task_id}**
  - Ответ: `{ "code": 200, "message": "Completed" }` или `{ "code": 204, "message": "Task is still running" }`

## Примечания
- Воркер отправляет результаты задач в очередь `task_results` в RabbitMQ.
- Для хранения задач используется SQLite (`async-service/data/tasks.db`).
- Сервисы обрабатывают ошибки (404, 500) и валидируют входные параметры.
- Для продакшен-использования рекомендуется заменить самоподписанные сертификаты на доверенные.