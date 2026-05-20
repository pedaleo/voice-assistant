# Voice Assistant (Omarchy/Linux)

Asistente de voz local inspirado en el vídeo de Nate Gentile "Mi PC Linux ahora trabaja por mí (CachyOS + IA)".

Pulsa un atajo de teclado, habla, y el PC te responde con voz. Puede controlar tu sistema, buscar información, cambiar temas, y más.

## Arquitectura

```
Alt+Z (habla) → Handy (STT) → voice-toggle.sh → assistant.py → Kiro CLI (LLM) → Piper (TTS) → Audio
```

1. **Alt+Z** — Inicia/detiene la grabación de voz
2. **Handy** — Transcribe tu voz a texto (modelo Parakeet, local)
3. **voice-toggle.sh** — Lee la transcripción de la DB de Handy y la pasa al script
4. **assistant.py** — Envía el texto al LLM y reproduce la respuesta con TTS
5. **Kiro CLI** — Procesa la pregunta (puede ejecutar comandos, buscar en internet, etc.)
6. **Piper TTS** — Convierte la respuesta a voz en español

## Requisitos

- [Omarchy](https://omarchy.org/) (Arch Linux + Hyprland)
- [Handy](https://github.com/pais-app/handy) (AppImage) — Speech-to-Text
- [Kiro CLI](https://kiro.dev/) — LLM con acceso a herramientas
- [Piper TTS](https://github.com/rhasspy/piper) — Text-to-Speech local
- mpv — Reproductor de audio
- wl-paste — Para leer el portapapeles (incluido en wl-clipboard)

## Instalación

### 1. Clonar este repo

```bash
git clone https://github.com/pedaleo/voice-assistant.git
cd voice-assistant
chmod +x assistant.py voice-toggle.sh
```

Clónalo donde prefieras (e.g. `~/Projects/`). Los scripts se auto-referencian, no dependen de una ruta fija.

### 2. Instalar Handy

Descarga el AppImage desde [las releases de Handy](https://github.com/pais-app/handy/releases):

```bash
mkdir -p ~/Applications
mv ~/Downloads/Handy_*.AppImage ~/Applications/
chmod +x ~/Applications/Handy_*.AppImage
```

Lánzalo una vez para que descargue el modelo de transcripción.

### 3. Instalar Kiro CLI

Sigue las instrucciones en [kiro.dev](https://kiro.dev/). Verifica que funciona:

```bash
kiro-cli chat --no-interactive "Hola"
```

### 4. Instalar Piper TTS

```bash
yay -S piper-tts
```

Cuando pregunte por `python-onnxruntime`, elige `python-onnxruntime-cpu` (opción 1) a menos que tengas GPU NVIDIA/AMD.

### 5. Descargar modelo de voz español

```bash
mkdir -p ~/.local/share/piper
curl -sL -o ~/.local/share/piper/es_ES-davefx-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx
curl -sL -o ~/.local/share/piper/es_ES-davefx-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json
```

Otros modelos de voz disponibles en: https://huggingface.co/rhasspy/piper-voices

### 6. Añadir atajo de teclado

Añade a `~/.config/hypr/bindings.conf`:

```
bindd = ALT, Z, Voice assistant, exec, /ruta/donde/clonaste/voice-assistant/voice-toggle.sh
```

Por ejemplo, si clonaste en `~/Projects/`:
```
bindd = ALT, Z, Voice assistant, exec, ~/Projects/voice-assistant/voice-toggle.sh
```

Hyprland recarga automáticamente al guardar.

### 7. Iniciar Handy

```bash
~/Applications/Handy_*.AppImage --start-hidden
```

Para que arranque con el sistema, Handy crea automáticamente un archivo en `~/.config/autostart/`.

## Uso

1. Pulsa **Alt+Z** — aparece notificación "Escuchando..."
2. Habla tu pregunta
3. Pulsa **Alt+Z** otra vez — procesa y responde con voz

### Ejemplos de cosas que puedes pedir

- "Qué hora es"
- "Cambia el tema a Tokyo Night"
- "Qué tiempo hace mañana"
- "Abre el navegador"
- "Cuánto espacio libre tengo en disco"

## Configuración

Edita `assistant.py` para cambiar el backend:

### Backend LLM

```python
# Kiro CLI (por defecto) — el más potente, puede ejecutar comandos
"llm_backend": "kiro",

# Ollama local — rápido, sin internet, menos inteligente
"llm_backend": "ollama",
"ollama_model": "llama3",

# API externa (OpenAI, OpenRouter, etc.)
"llm_backend": "api",
"api_url": "https://openrouter.ai/api/v1/chat/completions",
"api_key": "",  # O usa variable de entorno VOICE_ASSISTANT_API_KEY
"api_model": "openai/gpt-4o-mini",
```

### Backend TTS

```python
# Piper (por defecto) — buena calidad, local
"tts_backend": "piper",

# Espeak — robótico pero siempre disponible
"tts_backend": "espeak",
```

### Usar Ollama (alternativa local sin créditos)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

Cambia `"llm_backend": "ollama"` en el script. Es más rápido pero menos inteligente.

## Archivos

| Archivo | Función |
|---------|---------|
| `voice-toggle.sh` | Wrapper que orquesta el flujo completo |
| `assistant.py` | Script principal: recibe texto → LLM → TTS |
| `README.md` | Esta documentación |

## Cómo funciona voice-toggle.sh

El script usa un lockfile (`/tmp/voice_assistant.lock`) para saber si es la primera o segunda pulsación:

- **Primera pulsación**: guarda el ID de la última transcripción, activa Handy
- **Segunda pulsación**: para Handy, espera 3s, lee la nueva transcripción de la DB SQLite de Handy (`~/.local/share/com.pais.handy/history.db`), y la pasa a `assistant.py`

## Notas

- Handy transcribe mejor en inglés que en español. Nombres técnicos (Catppuccin, Omarchy) pueden salir mal escritos, pero Kiro es lo suficientemente inteligente para interpretar errores de transcripción.
- Cada pregunta por voz con backend "kiro" consume créditos de Kiro CLI.
- Con backend "ollama" todo es local y gratuito, pero menos capaz.
- El tiempo de respuesta con Kiro es ~10-25s. Con Ollama local ~5-15s.

## Troubleshooting

### No se escucha la respuesta
- Verifica que mpv funciona: `echo "test" | piper-tts --model ~/.local/share/piper/es_ES-davefx-medium.onnx --output_file /tmp/test.wav && mpv /tmp/test.wav`

### Handy no transcribe
- Verifica que está corriendo: `pgrep handy`
- Reinícialo: `pkill handy && ~/Applications/Handy_*.AppImage --start-hidden`

### "No se detectó transcripción nueva"
- Handy puede tardar en transcribir. Intenta hablar más tiempo o más claro.
- Revisa el log: `tail -20 ~/.local/share/com.pais.handy/logs/handy.log`

### Kiro no responde
- Verifica autenticación: `kiro-cli chat --no-interactive "test"`

## Licencia

MIT
