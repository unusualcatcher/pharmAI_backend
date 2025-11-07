from django.shortcuts import render

# backend/views.py
import json
import logging
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ai_agent.services.agent_service import stream_master_agent_response

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def stream_agent_chat(request):
    """
    POST endpoint that accepts JSON: {"query": "your question here"}
    Returns a StreamingHttpResponse using SSE-style 'data: {...}\n\n' messages.

    Example curl:
    curl -N -X POST http://127.0.0.1:8000/api/agent/stream/ \
      -H "Content-Type: application/json" \
      -d '{"query":"What is the market size for respiratory diseases?"}'
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest(json.dumps({"error": "invalid json"}), content_type="application/json")

    query = payload.get("query")
    if not query:
        return HttpResponseBadRequest(json.dumps({"error": "query field is required"}), content_type="application/json")

    # Stream the agent response as SSE
    streaming_iterable = stream_master_agent_response(query)
    response = StreamingHttpResponse(streaming_iterable, content_type="text/event-stream")
    # Recommended headers for SSE + dev-friendly CORS
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # for nginx: disable buffering
    response["Access-Control-Allow-Origin"] = "*"  # dev only; tighten in production
    response["Access-Control-Allow-Credentials"] = "true"
    return response


@csrf_exempt
@require_POST
def chat_agent(request):
    """
    Non-streaming endpoint: collects the full generated content and returns JSON.
    Useful for clients that cannot handle streaming.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest(json.dumps({"error": "invalid json"}), content_type="application/json")

    query = payload.get("query")
    if not query:
        return HttpResponseBadRequest(json.dumps({"error": "query field is required"}), content_type="application/json")

    # Collect full response by iterating the agent generator
    full = []
    try:
        for chunk in stream_master_agent_response(query):
            # stream_master_agent_response yields SSE bytes -> parse out the JSON payload inside.
            try:
                # decode bytes and drop the "data: " prefix if present
                s = chunk.decode("utf-8")
                # each chunk may contain 'data: {...}\n\n'
                for line in s.splitlines():
                    if line.startswith("data: "):
                        raw = line[len("data: "):]
                        obj = json.loads(raw)
                        if obj.get("chunk"):
                            full.append(obj["chunk"])
                        if obj.get("error"):
                            # include error and stop
                            return JsonResponse({"error": obj["error"]}, status=500)
                        if obj.get("done"):
                            pass
            except Exception:
                # fallback: append raw string
                full.append(str(chunk))
    except Exception as e:
        logger.exception("Error collecting non-stream response: %s", e)
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"response": "".join(full)})


@require_GET
def health_check(request):
    """
    Quick health endpoint to confirm the agent module is loaded.
    """
    try:
        # We attempt to import the master_agent so AppConfig.ready() has run
        from ai_agent.agents import master_agent  # noqa: F401
        return JsonResponse({"status": "healthy", "agent": "Master Agent"})
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
    
def demo(request):
    return render(request, 'backend/chatroom.html')
