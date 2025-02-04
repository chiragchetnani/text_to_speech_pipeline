import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import base64

app = FastAPI()

# Define the response model for the API
class ProcessResponse(BaseModel):
    session_id: str
    audio_stream_url: str

# Define the main function that interacts with both APIs
async def process_query(query: str, session_id: str):
    llm_api_url = "http://localhost:8002/query"
    tts_api_url = "http://localhost:8001/tts"
    
    # Call the LLM API
    async with httpx.AsyncClient() as client:
        llm_response = await client.get(llm_api_url, params={"query": query, "session_id": session_id})
        if llm_response.status_code == 200:
            llm_result = llm_response.json().get("response")
            print(f"LLM API Response: {llm_result}")
        else:
            raise HTTPException(status_code=llm_response.status_code, detail=f"Error in LLM API: {llm_response.text}")

    # Prepare TTS streaming generator
    async def tts_stream():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", tts_api_url, params={"query": llm_result}) as tts_response:
                if tts_response.status_code == 200:
                    async for chunk in tts_response.aiter_text():
                        # Decode each base64-encoded chunk
                        audio_data = base64.b64decode(chunk.strip())
                        yield audio_data
                else:
                    raise HTTPException(status_code=tts_response.status_code, detail=f"Error in TTS API: {tts_response.text}")

    return tts_stream

# Define the FastAPI route that uses the main function
@app.get("/process", response_model=ProcessResponse)
async def process_endpoint(query: str, session_id: str):
    tts_stream_generator = await process_query(query, session_id)

    # Return a streaming response for the audio data
    return StreamingResponse(tts_stream_generator(), media_type="audio/wav")

# Run the FastAPI app on port 8888
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8888, reload=True)