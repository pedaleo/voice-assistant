#!/usr/bin/env python3
"""
Asistente de voz: Handy STT → LLM → TTS → Audio Out
Uso: python3 assistant.py "texto transcrito por Handy"
"""

import sys
import json
import subprocess
import re
import time
import urllib.request
from pathlib import Path

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────

CONFIG = {
    # "kiro", "ollama" o "api"
    "llm_backend": "kiro",

    # Ollama config
    "ollama_url": "http://localhost:11434/api/generate",
    "ollama_model": "llama3",

    # API config (OpenAI-compatible)
    "api_url": "https://openrouter.ai/api/v1/chat/completions",
    "api_key": "",
    "api_model": "openai/gpt-4o-mini",

    # TTS config: "piper", "espeak" o "edge"
    "tts_backend": "edge",
    "piper_model": str(Path.home() / ".local/share/piper/kristin.onnx"),
    "edge_voice": "es-MX-DaliaNeural",

    # System prompt (para ollama/api)
    "system_prompt": "Eres un asistente de voz. Tu respuesta se lee en voz alta. Máximo 2 frases. Responde en español conversacional. Nunca deletrees rutas, comandos, URLs ni salidas técnicas. Resume todo en lenguaje natural.",
}

# ─── LLM ─────────────────────────────────────────────────────────────────────

SESSION_FILE = Path("/tmp/voice_assistant_session")
SESSION_TIMEOUT = 600  # 10 minutos sin actividad = sesión nueva

RESET_PHRASES = ["olvida todo", "reset", "nueva conversación", "empieza de cero", "borra el contexto"]


def should_reset_session(text: str) -> bool:
    """Comprueba si el usuario pide reset o si la sesión ha expirado."""
    lower = text.lower().strip()
    if any(phrase in lower for phrase in RESET_PHRASES):
        return True
    if SESSION_FILE.exists():
        last_used = SESSION_FILE.stat().st_mtime
        if time.time() - last_used > SESSION_TIMEOUT:
            return True
    return False


def reset_session():
    """Elimina las sesiones de Kiro CLI del asistente para empezar de cero."""
    SESSION_FILE.unlink(missing_ok=True)
    cwd = Path(__file__).resolve().parent
    # Listar sesiones y borrarlas
    result = subprocess.run(
        ["kiro-cli", "chat", "--list-sessions"],
        capture_output=True, text=True, cwd=cwd
    )
    for sid in re.findall(r'SessionId:\s*\x1b\[[\d;]*m([a-f0-9-]+)', result.stdout):
        subprocess.run(
            ["kiro-cli", "chat", "--delete-session", sid],
            capture_output=True, cwd=cwd
        )


def touch_session():
    """Actualiza el timestamp de la sesión."""
    SESSION_FILE.touch()


def query_kiro(text: str) -> str:
    """Usa Kiro CLI como backend LLM con sesión persistente."""
    prompt = (
        "Tu respuesta se va a leer en voz alta con TTS. REGLAS ESTRICTAS: "
        "Máximo 3 frases. Responde con personalidad, como un amigo listo que te echa una mano. "
        "Sé cercano, usa expresiones naturales y algo de humor cuando encaje. "
        "Nunca deletrees rutas, comandos, URLs ni salidas de terminal. "
        "Si ejecutas un comando, resume el resultado en lenguaje natural. "
        "No uses markdown, listas, ni formato. Solo texto plano conversacional en español. "
        "Contexto: el usuario usa Omarchy Linux con Hyprland. "
        "Temas disponibles: Aether, Catppuccin, Catppuccin Latte, Ethereal, Everforest, "
        "Flexoki Light, Gruvbox, Hackerman, Kanagawa, Lumon, Matte Black, Miasma, Nord, "
        "Osaka Jade, Retro 82, Ristretto, Rose Pine, Tokyo Night, Vantablack, White. "
        "Para cambiar tema usa: omarchy-theme-set \"nombre\". "
        "La pregunta del usuario (puede tener errores de transcripción de voz): " + text
    )
    cmd = ["kiro-cli", "chat", "--no-interactive", "--resume", "--trust-all-tools", "--wrap=never"]
    cmd.append(prompt)

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=60,
        cwd=Path(__file__).resolve().parent
    )

    # Limpiar códigos ANSI de la salida
    output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).strip()
    # Extraer respuesta: empieza en la primera línea con "> " e incluye todo lo que sigue
    lines = output.splitlines()
    response_started = False
    response_lines = []
    for line in lines:
        if line.strip().startswith(">"):
            response_started = True
            response_lines.append(line.lstrip("> ").strip())
        elif response_started:
            # Líneas de continuación (sin >) que son parte de la respuesta
            stripped = line.strip()
            if stripped and not stripped.startswith("▸") and not stripped.startswith("Time:"):
                response_lines.append(stripped)
            elif stripped.startswith("▸"):
                break  # Fin de la respuesta, empieza el footer
    return " ".join(response_lines).strip() if response_lines else output.splitlines()[-1].strip() if output else ""


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
    if CONFIG["llm_backend"] == "kiro":
        return query_kiro(text)
    elif CONFIG["llm_backend"] == "ollama":
        return query_ollama(text)
    return query_api(text)

# ─── TTS ─────────────────────────────────────────────────────────────────────

def speak_piper(text: str):
    """TTS con piper (local, rápido, buena calidad)."""
    wav = "/tmp/voice_assistant_tts.wav"
    subprocess.run(
        ["piper-tts", "--model", CONFIG["piper_model"], "--output_file", wav],
        input=text.encode(), capture_output=True
    )
    subprocess.run(["mpv", "--no-terminal", wav], capture_output=True)


def speak_edge(text: str):
    """TTS con Edge TTS (Microsoft, alta calidad, requiere internet)."""
    wav = "/tmp/voice_assistant_tts.wav"
    subprocess.run(
        ["edge-tts", "--voice", CONFIG["edge_voice"], "--text", text, "--write-media", wav],
        capture_output=True
    )
    subprocess.run(["mpv", "--no-terminal", wav], capture_output=True)


def speak_espeak(text: str):
    """Fallback con espeak."""
    subprocess.run(["espeak-ng", "-v", "es", text])


def speak(text: str):
    if CONFIG["tts_backend"] == "edge":
        speak_edge(text)
    elif CONFIG["tts_backend"] == "piper":
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

    # Comprobar si hay que resetear sesión
    if should_reset_session(text):
        reset_session()
        # Si fue un reset explícito, confirmar y salir
        lower = text.lower().strip()
        if any(phrase in lower for phrase in RESET_PHRASES):
            speak("Listo, he olvidado todo. Empezamos de cero.")
            touch_session()
            sys.exit(0)

    try:
        response = query_llm(text)
        touch_session()
        if response:
            speak(response)
        else:
            subprocess.run(["notify-send", "🎙️ Asistente", "Sin respuesta"])
    except Exception as e:
        subprocess.run(["notify-send", "🎙️ Asistente", f"Error: {e}"])
        sys.exit(1)


if __name__ == "__main__":
    main()
