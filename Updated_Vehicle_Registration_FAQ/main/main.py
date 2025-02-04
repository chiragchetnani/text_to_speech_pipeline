import httpx
import asyncio
import base64

async def main(query: str, session_id: str):
    # Define endpoints
    llm_api_url = "http://localhost:8002/query"
    tts_api_url = "http://localhost:8001/tts"
    
    # First, query the LLM API
    async with httpx.AsyncClient() as client:
        response = await client.get(llm_api_url, params={"query": query, "session_id": session_id})
        if response.status_code == 200:
            llm_response = response.json().get("response")
            print(f"LLM API Response: {llm_response}")
        else:
            raise Exception(f"Error in LLM API: {response.status_code}, {response.text}")
    
    # Then, pass the LLM response to the TTS API and receive the streamed audio response
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", tts_api_url, params={"query": llm_response}) as tts_response:
            if tts_response.status_code == 200:
                with open("output.wav", "wb") as f:
                    async for chunk in tts_response.aiter_text():
                        # Decode the base64 chunk back to binary audio data
                        audio_data = base64.b64decode(chunk.strip())
                        f.write(audio_data)
                print("TTS API Response: Audio file saved as 'output.wav'")
            else:
                raise Exception(f"Error in TTS API: {tts_response.status_code}, {tts_response.text}")

    return {
        "session_id": session_id,
        "LLM_Response": llm_response,
        "TTS_Output_File": "output.wav"
    }

# Run the main function
query_text = "Hello, aur kaise ho"
session_id = "session_1"
result = asyncio.run(main(query_text, session_id))
print(result)