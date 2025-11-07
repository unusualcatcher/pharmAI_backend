# ai_agent/services/agent_service.py
import json
import logging
from typing import Iterable

from ..agents import master_agent

logger = logging.getLogger(__name__)

def _chunk_to_payload(chunk) -> str:
    """
    Normalize a yielded chunk into a string payload.
    - If the chunk is LangChain/BaseMessage-like, extract `.content`.
    - If it's dict/list, encode as JSON string.
    - Otherwise str(chunk).
    """
    try:
        # If it's an object with `.content` attribute (LangChain messages)
        if hasattr(chunk, "content"):
            content = chunk.content
            # content might be bytes or other types
            return content if isinstance(content, str) else str(content)
        # If it's a dict/list — convert to compact JSON
        if isinstance(chunk, (dict, list)):
            return json.dumps(chunk, ensure_ascii=False)
        # Otherwise convert to string
        return str(chunk)
    except Exception as e:
        logger.exception("Error converting chunk to payload: %s", e)
        return f"[error serializing chunk: {e}]"

def stream_master_agent_response(query: str) -> Iterable[bytes]:
    """
    Yield SSE-style data chunks (bytes) that can be returned via Django's StreamingHttpResponse
    or via an ASGI endpoint.

    We iterate master_agent.invoke(query) which is expected to be a generator that yields:
      - text chunks (str) or
      - LangChain BaseMessage-like objects with `.content` property
      - or dict/list payloads

    Each yielded item is serialized into a JSON object and emitted as an SSE `data:` line:
      data: {"chunk": "..."}\n\n

    After the generator completes we emit a final {"done": true} message.
    """
    try:
        # master_agent.invoke(...) yields chunks (generator). Use that directly.
        stream_gen = master_agent.invoke(query)
    except Exception as e:
        # If master_agent.invoke itself fails immediately, yield an error chunk
        err = {"error": f"Agent invocation failed: {e}"}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")
        yield f"data: {json.dumps({'done': True})}\n\n".encode("utf-8")
        return

    # iterate generator and yield SSE chunks
    try:
        for chunk in stream_gen:
            payload_str = _chunk_to_payload(chunk)
            # Wrap the payload as JSON with a top-level "chunk" field so frontend can parse easily
            sse = f"data: {json.dumps({'chunk': payload_str}, ensure_ascii=False)}\n\n"
            yield sse.encode("utf-8")
    except GeneratorExit:
        # Consumer disconnected; just stop
        logger.info("Client disconnected during streaming.")
        return
    except Exception as e:
        logger.exception("Error while streaming agent response: %s", e)
        err = {"error": f"Streaming error: {str(e)}"}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode("utf-8")

    # final done message
    yield f"data: {json.dumps({'done': True})}\n\n".encode("utf-8")
