from groq import Groq 
from fastapi import FastAPI
import uvicorn
from scripts.llm.runner import run_groq
from redis import Redis
from scripts.services.services import save_history, load_history
from scripts.config.config import LLM_api
import requests
import asyncio
import time

# Redis client
redis_client = Redis(
    host='localhost', 
    port=6379, 
    decode_responses=True
)

# Groq client
groq_client = Groq(api_key=LLM_api)
prompt = open('assets/prompt.txt').read()

# In-memory session storage
active_sessions = {}

def get_context(query, collection_name="rag", k=1):
    url = "http://localhost:8003/similarity_search"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "collection_name": collection_name,
        "k": k
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")

app = FastAPI()

@app.get('/')
def read_root():
    return {'message': 'Welcome to the LLM API'}

@app.get('/query')
async def query(query: str, session_id: str):
    global prompt
    
    context = get_context(query)
    print(f'|LOG : RECEIVED QUERY : {query}')
    
    # Check for session in memory
    if session_id in active_sessions:
        # Update the chat history and reset the activity timer
        active_sessions[session_id]['history'].append({'role': 'user', 'content': query})
        active_sessions[session_id]['last_active'] = time.time()
    else:
        # Load history from Redis if it's a new session in memory
        history = load_history(redis_client, session_id)
        active_sessions[session_id] = {
            'history': history + [{'role': 'user', 'content': query}],
            'last_active': time.time()
        }
    
    # Save user query to Redis
    save_history(redis_client, session_id, {'role': 'user', 'content': query})
    
    # Prepare the query with context and chat history
    query_text = f'''{prompt}
    
    You have to answer the question based on the chat history and context
    
    Chat History: /<{active_sessions[session_id]["history"]}>/
    Query: /<{query}>/
    '''
    
    response = run_groq(query_text, groq_client)
    print(f'|LOG : SENDING RESPONSE : {response}')
    
    # Save assistant response to in-memory session
    active_sessions[session_id]['history'].append({'role': 'assistant', 'content': response})
    active_sessions[session_id]['last_active'] = time.time()
    
    # Save assistant response to Redis
    save_history(redis_client, session_id, {'role': 'assistant', 'content': response})
    
    return {'response': response}

async def monitor_sessions():
    """Background task to monitor and save inactive sessions to Redis."""
    while True:
        current_time = time.time()
        inactive_sessions = [
            session_id for session_id, session in active_sessions.items()
            if current_time - session['last_active'] > 120
        ]
        
        for session_id in inactive_sessions:
            # Save to Redis if inactive
            history = active_sessions[session_id]['history']
            for entry in history:


                save_history(redis_client, session_id, entry)
            
            # Remove from in-memory storage
            del active_sessions[session_id]
        
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_sessions())

if __name__ == '__main__':
    uvicorn.run('app:app', host='0.0.0.0', port=8002, reload=True)
