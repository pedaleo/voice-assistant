# Voice Assistant (Omarchy/Linux)

Asistente de voz local inspirado en el vídeo de Nate Gentile "Mi PC Linux ahora trabaja por mí (CachyOS + IA)".

Pulsa un atajo de teclado, habla, y el PC te responde con voz. Puede controlar tu sistema, buscar información, cambiar temas, y más.

## Arquitectura

```
Alt+Z (habla) → Handy (STT) → voice-toggle.sh → assistant.py → Kiro CLI (LLM) → Edge TTS → Audio
```

1. **Alt+Z** — Inicia/detiene la grabación de voz
2. **Handy** — Transcribe tu voz a texto (modelo Parakeet, local)
3. **voice-toggle.sh** — Lee la transcripción de la DB de Handy y la pasa al script
4. **assistant.py** — Envía el texto al LLM y reproduce la respuesta con TTS
5. **Kiro CLI** — Procesa la pregunta (puede ejecutar comandos, buscar en internet, etc.)
6. **Edge TTS** — Convierte la respuesta a voz (Microsoft, alta calidad)

## Requisitos

- [Omarchy](https://omarchy.org/) (Arch Linux + Hyprland)
- [Handy](https://github.com/pais-app/handy) (AppImage) — Speech-to-Text
- [Kiro CLI](https://kiro.dev/) — LLM con acceso a herramientas
- [Edge TTS](https://github.com/rany2/edge-tts) — Text-to-Speech (Microsoft, requiere internet)
- [Piper TTS](https://github.com/rhasspy/piper) — Text-to-Speech local (alternativa offline)
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

### 4. Instalar Edge TTS

```bash
pip install edge-tts --break-system-packages
```

Verifica que funciona:

```bash
edge-tts --voice "es-MX-DaliaNeural" --text "Hola, soy tu asistente" --write-media /tmp/test.wav && mpv /tmp/test.wav
```

### 5. (Opcional) Instalar Piper TTS como fallback offline

```bash
yay -S piper-tts
```

Descarga un modelo de voz:

```bash
mkdir -p ~/.local/share/piper
curl -sL -o ~/.local/share/piper/kristin.onnx \
  https://sfo3.digitaloceanspaces.com/bkmdls/kristin.onnx
curl -sL -o ~/.local/share/piper/kristin.onnx.json \
  https://sfo3.digitaloceanspaces.com/bkmdls/kristin.onnx.json
```

### 6. Añadir atajo de teclado

Añade a `~/.config/hypr/bindings.conf` la ruta **absoluta** donde clonaste el repo:

```
bindd = ALT, Z, Voice assistant, exec, ~/Projects/personal/voice-assistant/voice-toggle.sh
```

> ⚠️ La ruta debe coincidir exactamente con la ubicación del repo clonado. Si lo tienes en otro sitio, ajústala.

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

### Sesión y memoria

El asistente mantiene contexto entre preguntas consecutivas (puedes hacer preguntas de seguimiento). La sesión se resetea automáticamente tras **10 minutos** de inactividad.

Para resetear manualmente, di cualquiera de estas frases:
- "Olvida todo"
- "Reset"
- "Nueva conversación"
- "Empieza de cero"
- "Borra el contexto"

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
# Edge TTS (por defecto) — alta calidad, requiere internet
"tts_backend": "edge",
"edge_voice": "es-MX-DaliaNeural",

# Piper — buena calidad, local, sin internet
"tts_backend": "piper",
"piper_model": "~/.local/share/piper/kristin.onnx",

# Espeak — robótico pero siempre disponible
"tts_backend": "espeak",
```

### Voces Edge TTS disponibles

| Voz | Idioma | Tipo |
|-----|--------|------|
| `es-MX-DaliaNeural` | Español México | Femenina, suave |
| `es-ES-AlvaroNeural` | Español España | Masculina |
| `es-ES-ElviraNeural` | Español España | Femenina |
| `es-ES-XimenaNeural` | Español España | Femenina |
| `en-GB-RyanNeural` | Inglés UK | Masculina, estilo Jarvis |
| `en-US-AndrewNeural` | Inglés US | Masculina, cálida |
| `en-US-ChristopherNeural` | Inglés US | Masculina, autoridad |

Lista completa: `edge-tts --list-voices`

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
- Edge TTS requiere internet pero no tiene límite de uso ni necesita API key.
- El tiempo de respuesta con Kiro es ~10-25s. Con Ollama local ~5-15s.

## Troubleshooting

### No se escucha la respuesta
- Verifica Edge TTS: `edge-tts --voice "es-MX-DaliaNeural" --text "test" --write-media /tmp/test.wav && mpv /tmp/test.wav`
- Si no hay internet, cambia a `"tts_backend": "piper"` en el script.

### Handy no transcribe
- Verifica que está corriendo: `pgrep handy`
- Reinícialo: `pkill handy && ~/Applications/Handy_*.AppImage --start-hidden`

### "No se detectó transcripción nueva"
- Handy puede tardar en transcribir. Intenta hablar más tiempo o más claro.
- Revisa el log: `tail -20 ~/.local/share/com.pais.handy/logs/handy.log`

### Kiro no responde
- Verifica autenticación: `kiro-cli chat --no-interactive "test"`

### Respuesta cortada
- Si la respuesta se corta, puede ser un problema de parsing. Verifica la salida cruda:
  ```bash
  kiro-cli chat --no-interactive --wrap=never "tu pregunta" 2>/dev/null | cat -A
  ```

## Licencia

MIT
