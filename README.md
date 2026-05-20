# Voice Assistant (Omarchy/Linux)

Asistente de voz local inspirado en el vídeo de Nate Gentile "Mi PC Linux ahora trabaja por mí".

Pulsa un atajo de teclado, habla, y el PC te responde con voz.

## Arquitectura

```
Alt+Z → Handy (STT) → Python script → Ollama/API (LLM) → Piper (TTS) → Audio
```

## Requisitos

- [Omarchy](https://omarchy.org/) (Arch Linux + Hyprland)
- [Handy](https://github.com/pais-app/handy) (AppImage) — Speech-to-Text
- [Ollama](https://ollama.com/) + llama3 — LLM local
- [Piper TTS](https://github.com/rhasspy/piper) — Text-to-Speech local
- mpv — Reproductor de audio

## Instalación

### 1. Clonar este repo

```bash
git clone https://github.com/pedaleo/voice-assistant.git ~/scripts/voice-assistant
```

### 2. Instalar dependencias

```bash
# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Piper TTS
yay -S piper-tts

# Modelo de voz español
mkdir -p ~/.local/share/piper
wget -P ~/.local/share/piper https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx
wget -P ~/.local/share/piper https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json
```

### 3. Instalar Handy

```bash
mkdir -p ~/Applications
# Descargar el AppImage desde https://github.com/pais-app/handy/releases
chmod +x ~/Applications/Handy_0.8.3_amd64.AppImage
```

### 4. Añadir atajo de teclado

Añadir a `~/.config/hypr/bindings.conf`:

```
bindd = ALT, Z, Voice assistant, exec, ~/scripts/voice-assistant/voice-toggle.sh
```

## Uso

1. Pulsa `Alt+Z` — aparece notificación "Escuchando..."
2. Habla tu pregunta
3. Pulsa `Alt+Z` otra vez — el asistente procesa y responde con voz

## Configuración

Edita `assistant.py` para cambiar:

### LLM Backend

```python
# Local con Ollama (por defecto)
"llm_backend": "ollama",
"ollama_model": "llama3",

# O usar API externa (OpenAI, OpenRouter, etc.)
"llm_backend": "api",
"api_url": "https://openrouter.ai/api/v1/chat/completions",
"api_key": "tu-key",
"api_model": "openai/gpt-4o-mini",
```

### TTS

```python
# Piper local (por defecto)
"tts_backend": "piper",

# Espeak (fallback, robótico)
"tts_backend": "espeak",
```

### Alternativas TTS más realistas

- **ElevenLabs API** — Calidad premium, requiere API key
- **Kokoro-82M** — Local, calidad muy buena, requiere PyTorch

## Archivos

| Archivo | Función |
|---------|---------|
| `voice-toggle.sh` | Wrapper que orquesta el flujo (binding → Handy → script) |
| `assistant.py` | Script principal: recibe texto → LLM → TTS |

## Notas

- Handy guarda las transcripciones en `~/.local/share/com.pais.handy/history.db`
- El wrapper lee la última transcripción directamente de esa DB
- Ollama debe estar corriendo (`ollama serve` o el servicio systemd)
- En CPU Intel el tiempo de respuesta es ~10-20s con llama3 8B

## Licencia

MIT
