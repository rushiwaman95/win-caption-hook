"""
Flask routes - Orchestrator + Checkpoint System
"""

import json
import time
from flask import Blueprint, render_template, jsonify, Response, request, stream_with_context
import core.state as state
from api.groq_client import stream_chat

bp = Blueprint('api', __name__)


@bp.route('/')
def home():
    return render_template('index.html')


@bp.route('/events')
def caption_stream():
    """SSE stream for captions + orchestrator state"""

    client_id = int(time.time() * 1000) % 10000
    print(f"📡 SSE connected [ID:{client_id}]")

    def generate():
        last_text = ""
        last_state = None

        yield f"data: {json.dumps({'type': 'connected'})}\n\n"

        while True:
            try:
                with state.LOCK:
                    current_text = state.LIVE_TEXT
                    current_state = state.ORCHESTRATOR_STATE.value
                    silence_detected = state.is_silence_detected()

                # Send text updates
                if current_text != last_text:
                    payload = json.dumps({'type': 'caption', 'text': current_text})
                    yield f"data: {payload}\n\n"
                    last_text = current_text

                # Send state updates
                if current_state != last_state or silence_detected:
                    payload = json.dumps({
                        'type': 'state',
                        'state': current_state,
                        'silence': silence_detected
                    })
                    yield f"data: {payload}\n\n"
                    last_state = current_state

                time.sleep(0.1)

            except GeneratorExit:
                print(f"❌ SSE disconnected [ID:{client_id}]")
                break
            except Exception as e:
                print(f"❌ SSE error [ID:{client_id}]: {e}")
                break

    response = Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@bp.route('/api/chat', methods=['POST'])
def chat():
    """Send message to AI"""

    request_id = int(time.time() * 1000) % 10000

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Empty message'}), 400

        print(f"\n{'='*70}")
        print(f"💬 CHAT [{request_id}]")
        print(f"{'='*70}")
        print(f"📥 Message: {user_message[:80]}...")

        # Update checkpoint + set AI streaming state
        state.update_checkpoint(user_message)
        state.set_state(state.OrchestratorState.AI_STREAMING)
        state.pause_capture()

        print(f"📌 Checkpoint updated")

        messages = [{"role": "user", "content": user_message}]

        def generate():
            try:
                full_response = ""
                chunk_count = 0

                for chunk in stream_chat(messages):
                    chunk_count += 1
                    full_response += chunk
                    payload = json.dumps({'type': 'token', 'content': chunk})
                    yield f"data: {payload}\n\n"

                print(f"✅ AI complete: {chunk_count} chunks")

                state.add_chat_message("user", user_message)
                state.add_chat_message("assistant", full_response)

                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                print(f"{'='*70}\n")

            except Exception as e:
                error_msg = str(e)
                print(f"❌ AI error: {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

            finally:
                # Resume capture + reset to listening state
                state.set_state(state.OrchestratorState.LISTENING)
                state.resume_capture()
                print(f"▶️  Capture resumed")

        response = Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'
        response.headers['Connection'] = 'keep-alive'
        return response

    except Exception as e:
        state.set_state(state.OrchestratorState.LISTENING)
        state.resume_capture()
        print(f"❌ Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/skip', methods=['POST'])
def skip():
    """Skip current text (don't send to AI, just checkpoint it)"""

    try:
        data = request.get_json()
        text_to_skip = data.get('text', '').strip()

        print(f"⏭️  SKIP: '{text_to_skip[:50]}...'")

        # Update checkpoint without sending to AI
        state.update_checkpoint(text_to_skip)
        state.set_state(state.OrchestratorState.LISTENING)
        state.reset_silence()

        return jsonify({'success': True, 'checkpoint': state.get_checkpoint()[:100]})

    except Exception as e:
        print(f"❌ Skip error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/chat/clear', methods=['POST'])
def clear_history():
    """Clear everything"""
    print("🗑️  Clearing all state")
    state.reset_all()
    return jsonify({'success': True})


@bp.route('/api/stats')
def stats():
    """Get orchestrator stats"""
    return jsonify(state.get_stats())


@bp.route('/health')
def health():
    return jsonify({'status': 'ok'})


@bp.route('/debug/caption')
def debug_caption():
    """Debug endpoint"""
    return jsonify(state.get_stats())

@bp.route('/api/keys/stats')
def key_stats():
    """Get API key rotation statistics"""
    from api.key_manager import key_manager
    return jsonify(key_manager.get_stats())