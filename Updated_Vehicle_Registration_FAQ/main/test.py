import httpx
import asyncio
import time

async def client_request(query: str):
    api_url = "http://localhost:8888/process"
    
    # Record the start time
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, params={"query": query , "session_id" : "session_2"})
        
        # Calculate the time taken
        end_time = time.time()
        time_taken = end_time - start_time
        
        if response.status_code == 200:
            # Save the audio file returned by the server
            with open("output.wav", "wb") as f:
                f.write(response.content)
            print("Audio file saved as 'output.wav'")
        else:
            print(f"Error: {response.status_code}, {response.text}")
        
        # Print the time taken for the request
        print(f"Time taken: {time_taken:.2f} seconds")

# Run the client request
query_text = "भाई, ड्राइविंग लाइसेंस कैसे बनवाए?"
asyncio.run(client_request(query_text))
