#!/bin/bash

# <----------------Install Redis Server----------------->
sudo apt update
sudo apt upgrade
sudo apt install redis-server -y

# <----------------Start Redis Server----------------->
redis-server &
echo "Redis Server started on port 6379"

# <----------------Install Python Libraries----------------->
pip install -r requirements.txt

# <----------------Start Chroma Server----------------->
cd chroma_api
python app.py &
echo "Chroma Server started on port 8003"
cd ..

# <----------------Start LLM Server----------------->
cd llm
python app.py &
echo "LLM Server started on port 8002"
cd ..

# <----------------Start TTS Server----------------->
cd tts
python app.py &
echo "TTS Server started on port 8001"
cd ..

# <----------------Start Main Server----------------->
cd main
python app.py &
echo "Main Server started on port 8888"
cd ..

# Wait for all background processes
echo "All servers have been started. Use 'ps aux | grep python' to see running processes"
echo "To stop all servers, use: pkill python"

# Keep the script running
wait