# AI Conversational System with TTS

A distributed conversational AI system built around the LLaMA 3 70B model, featuring text-to-speech capabilities and intelligent context management. The system combines vector search, session management, and voice synthesis to deliver contextually aware responses in both text and speech formats.

## Core Architecture

The system operates through five interconnected services:

* Session management is handled through a dual-layer caching system using Redis `(6379)`. Active conversations are also kept in an in-memory buffer for quick access, while inactive sessions `(120 seconds timeout)` are automatically persisted to Redis for efficient resource management.

* The Chroma Vector Database `(8003)` enhances response relevance by providing semantic search capabilities. Through its `/similarity-search` endpoint, it identifies and retrieves contextually relevant information that helps shape the model's responses.

* The LLM Service `(8002)` powers the system's intelligence using the LLaMA 3 70B model via Groq. It processes queries by combining conversation history with contextual information from the vector database, utilizing the model's 8192 token context window to generate coherent responses with `GET` `/query` endpoint.

* The TTS Service `(8002)` converts generated text to speech using `Edge TTS` with the `hi-IN-SwaraNeural` voice model. It's designed to stream audio output, ensuring smooth delivery of voice responses.

* The Main API `(8888)` serves as the primary entry point, handling all client interactions through its `GET` `/process` endpoint.

## Operational Flow

1. User requests arrive at the `Main API` with a `session ID` and `input text`.
2. The `LLM Service` retrieves conversation history from cache or `Redis`.
3. Relevant context is gathered through `vector similarity search`.
4. `LLaMA 3 70B 8192` generates a response based on the combined `context` and `chat hisotry`.
5. The response is converted to speech while being sent back to the user.
6. Both text and audio are streamed back to the client.

This architecture enables natural, context-aware conversations with voice output while maintaining efficient resource usage through intelligent caching and session management.

# System Architecture 
```
                                  ┌─────────────────┐
                                  │   Redis Cache   │
                                  │    (6379)       │
                                  └────────┬────────┘
                                           │
┌──────────────┐    ┌───────────────┐      │      ┌────────────────┐
│   Main API   │    │    LLM API    │      │      │  Chroma VDB    │
│   (8888)     │◄──►│    (8002)     │◄─────┴      │    (8003)      │
│  /process    │    │    /query     │◄───────────►│/similarity-search│
└───────┬──────┘    └──────┬────────┘             └────────────────┘
        │                  │                              
        │                  │                              
        │                  │                              
        │                  ▼                              
        │           ┌────────────┐                        
        │           │ Groq API   │
        │           │(LLaMA 3 70B)│
        │           └────────────┘
        ▼
┌────────────────┐
│    TTS API     │
│    (8002)      │◄───────────┐
│     /tts       │            │
└───────┬────────┘     ┌──────┴─────┐
        │              │  Edge TTS   │
        └──────────────►│(hi-IN-Swara)│
                       └─────────────┘
```

This architecture diagram illustrates the flow of data and interactions between the various components of the system. 

<img src = 'assets/LLM System Architecture.jpg'>

# Getting Started 

```bash
./start.sh
```