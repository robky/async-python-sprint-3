# Консольный чат (server/client)

Приложение для получения и обработки сообщений от клиента.

## Описание

### `Сервер`

Сервис, который обрабатывает поступающие запросы от клиентов.

- Подключенный клиент добавляется в «общий» чат, где находятся ранее подключенные клиенты.
- После подключения новому клиенту доступны последние N cообщений из общего чата (20, по умолчанию).

<details>
<summary> Список возможных команд </summary>

1. Выйти из чата.

```
/q
```

2. Получить помощь по командам.

```
/h
```

3. Отправить сообщение определенному пользователю (приватное сообщение).

```
/p <пользователь> <сообщение>
```
</details>


### `Клиент`

Сервис, который умеет подключаться к серверу для обмена сообщениями с другими клиентами.

- После подключения клиент может отправлять сообщения в «общий» чат.
- Возможность отправки сообщения в приватном чате (1-to-1) любому участнику из общего чата.
- Пользователь может подключиться с двух и более клиентов одновременно.

## Перед запуском

1. Переименовать файл .env.example в .env
```bash
mv .env.example .env
```

2. Заполнить файл .env актуальными данными согласно примера.