
import json 

def save_history(redis_client , session_id , message) : 

    message = json.dumps(message)

    redis_client.rpush(
        session_id , message
    )

def load_history(redis_client , session_id , limit = 10) : 

    messages = redis_client.lrange(session_id, 0, -1)

    return [json.loads(msg) for msg in messages][- (limit * 2):]
