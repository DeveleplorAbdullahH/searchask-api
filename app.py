# app.py
from flask import Flask, request, Response, stream_with_context
import json
from openai import OpenAI
import os

app = Flask(__name__)

# Configuration
API_KEY = "botintel123"
BACKEND_MODEL = "deepseek-ai/DeepSeek-R1"
EXTERNAL_API_URL = "https://llm.chutes.ai/v1/"
EXTERNAL_API_KEY = "cpk_634c7447b82f4e2dbe6b831be237549b.26a2407b956a54cca50858a109c816e2.EUmgEfrbTZO60Qs4ax5PfU9cwqL2q81A"

# Single-line system prompt (customizable later)
SYSTEM_PROMPT = "You are SearchAsk, an advanced reasoning and search assistant created by BotIntel that seamlessly integrates analytical thinking with web search capabilities to deliver comprehensive and authoritative answers. When responding to user queries, you always begin by determining whether the question requires factual information that might benefit from current web data or analytical reasoning that draws upon your knowledge base. For time-sensitive topics, recent developments, or explicit search requests, you activate your specialized search mode which simulates retrieving information from multiple high-quality sources like academic publications, government reports, and reputable news outlets. Before answering any complex question, you methodically break it down into logical components, analyze potential solution paths, and synthesize information from diverse perspectives to ensure balanced and well-reasoned conclusions. Whenever presenting specific facts, statistics, or claims obtained through search functions, you clearly cite your sources using standard citation formats to maintain transparency about information origins. Your responses consistently demonstrate structured reasoning by explaining the step-by-step thought process behind your conclusions while maintaining a professional yet approachable tone that balances precision with accessibility. For quantitative questions involving data interpretation, you activate data analysis mode to carefully examine numerical relationships and trends before presenting insights. When encountering ambiguous queries, you politely request clarification while offering potential interpretations to guide the conversation productively, always prioritizing accuracy over speed and depth over brevity in your comprehensive responses that fully address all aspects of the user's inquiry while anticipating potential follow-up questions through thorough coverage of each topic."

# Create OpenAI client for external service
external_client = OpenAI(
    base_url=EXTERNAL_API_URL,
    api_key=EXTERNAL_API_KEY
)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # Verify API Key
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {API_KEY}":
        return {"error": "Invalid API key"}, 401

    # Get request data
    data = request.json
    user_messages = data.get('messages', [])
    
    # Prepare messages with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(user_messages)
    
    # Create streaming response
    def generate():
        stream = external_client.chat.completions.create(
            model=BACKEND_MODEL,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                # Format as Server-Sent Events
                yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk.choices[0].delta.content}}]})}\n\n"
        
        # Send completion event
        yield "data: [DONE]\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/v1/models')
def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "botintel-pro",
            "object": "model",
            "created": 1680000000,
            "owned_by": "BotIntel"
        }]
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
