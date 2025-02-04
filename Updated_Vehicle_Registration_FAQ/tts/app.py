import asyncio
import uvicorn
from fastapi import FastAPI
from edge_tts import Communicate
from fastapi.responses import StreamingResponse
import base64

app = FastAPI()

async def tts_stream(text: str):
    communicate = Communicate(text, 'hi-IN-SwaraNeural')  # Hindi voice

    # Stream each audio chunk
    async for chunk in communicate.stream():

        print(chunk)

        if chunk['type'] == 'audio' : 
        # Get the audio data from each chunk
            audio_chunk = chunk["data"]

            # Encode the chunk in base64 if needed
            base64_audio_chunk = base64.b64encode(audio_chunk).decode("utf-8")

            # Yield each chunk in real-time
            yield base64_audio_chunk + "\n"  # Adding a newline to distinguish chunks

@app.get("/")
def read_root():
    return {"message": "Welcome to the TTS API"}

@app.get("/tts")
async def tts_endpoint(query: str):
    # Stream the response with StreamingResponse
    return StreamingResponse(tts_stream(query), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
