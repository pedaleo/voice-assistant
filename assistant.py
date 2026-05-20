#!/usr/bin/env python3
"""
Asistente de voz: Handy STT → LLM → TTS → Audio Out
Uso: python3 assistant.py "texto transcrito por Handy"
"""

import sys
import json
import subprocess
import urllib.request
from pathlib import Path

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────

CONFIG = {
    # "ollama" o "api"
    "llm_backend": "ollama",

    # Ollama config
    "ollama_url": "http://localhost:11434/api/generate",
    "ollama_model": "llama3",

    # API config (OpenAI-compatible: OpenAI, Anthropic via proxy, OpenRouter, etc.)
    "api_url": "https://openrouter.ai/api/v1/chat/completions",
    "api_key": "",  # Pon tu key aquí o en env: VOICE_ASSISTANT_API_KEY
    "api_model": "openai/gpt-4o-mini",

    # TTS config
    # "piper" (local) o "espeak" (fallback)
    "tts_backend": "piper",
    "piper_model": str(Path.home() / ".local/share/piper/es_ES-davefx-medium.onnx"),

    # System prompt
    "system_prompt": "Eres un asistente de voz conciso. Responde en español, de forma breve y directa. No uses markdown ni formato especial.",
}

# ─── LLM ─────────────────────────────────────────────────────────────────────

def query_ollama(text: str) -> str:
    payload = json.dumps({
        "model": CONFIG["ollama_model"],
        "prompt": text,
        "system": CONFIG["system_prompt"],
        "stream": False,
    }).encode()
    req = urllib.request.Request(CONFIG["ollama_url"], data=payload,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["response"]


def query_api(text: str) -> str:
    import os
    api_key = CONFIG["api_key"] or os.environ.get("VOICE_ASSISTANT_API_KEY", "")
    payload = json.dumps({
        "model": CONFIG["api_model"],
        "messages": [
            {"role": "system", "content": CONFIG["system_prompt"]},
            {"role": "user", "content": text},
        ],
    }).encode()
    req = urllib.request.Request(CONFIG["api_url"], data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def query_llm(text: str) -> str:
    if CONFIG["llm_backend"] == "ollama":
        return query_ollama(text)
    return query_api(text)

# ─── TTS ─────────────────────────────────────────────────────────────────────

def speak_piper(text: str):
    """TTS con piper (local, rápido, buena calidad)."""
    wav = "/tmp/voice_assistant_tts.wav"
    proc = subprocess.run(
        ["piper-tts", "--model", CONFIG["piper_model"], "--output_file", wav],
        input=text.encode(), capture_output=True
    )
    if proc.returncode == 0:
        subprocess.run(["mpv", "--no-terminal", wav], capture_output=True)


def speak_espeak(text: str):
    """Fallback con espeak (robótico pero siempre disponible)."""
    subprocess.run(["espeak-ng", "-v", "es", text])


def speak(text: str):
    if CONFIG["tts_backend"] == "piper":
        speak_piper(text)
    else:
        speak_espeak(text)

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: assistant.py 'texto transcrito'")
        sys.exit(1)

    text = " ".join(sys.argv[1:])
    if not text.strip():
        sys.exit(0)

    try:
        response = query_llm(text)
        speak(response)
    except Exception as e:
        # Notificar error por notificación del sistema
        subprocess.run(["notify-send", "Voice Assistant", f"Error: {e}"])
        sys.exit(1)


if __name__ == "__main__":
    main()
