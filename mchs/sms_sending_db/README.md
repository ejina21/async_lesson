# Database layer for SMS mailing service

The database layer provides a single `Database` class to interact with Redis DB.

## Database methods

Following async methods are available:


### `add_sms_mailing(…)`

The method adds to Redis multiple records representing a new SMS mailing.

### `get_pending_sms_list()`

The method gets from Redis all pending messages from all mailings at once.

### `update_sms_status_in_bulk(…)`

Method receives list of tuples `(sms_id, phone, status)`. Usage example:

```python
await db.update_sms_status_in_bulk([
    # [sms_id, phone_number, status]
    [sms_id, phone_number1, 'failed'],
    [sms_id, phone_number2, 'pending'],
    [another_sms_id, phone_number2, 'delivered'],
    # Status possible values: 'failed', 'pending' and 'delivered'
])
```

### `get_sms_mailings(…)`

Method loads from DB all mailings was saved before. It returns list of dicts — one dict per found mailing.

### `list_sms_mailings()`

The method returns a list of sms_id for all registered SMS mailings.

## Examples

Checkout usage examples in `example.py` file. Install and run it with command:

```sh
$ pip install -r requirements.txt
$ python example.py --address="redis://..." --password="..."
```
