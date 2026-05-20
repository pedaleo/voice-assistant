#!/bin/bash
# Voice Assistant wrapper
# Flujo: Alt+Z toggle → Handy graba/para → lee última transcripción de DB → LLM → TTS

LOCKFILE="/tmp/voice_assistant.lock"
HANDY="$HOME/Applications/Handy_0.8.3_amd64.AppImage"
DB="$HOME/.local/share/com.pais.handy/history.db"

get_last_transcription() {
    python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
cur = conn.cursor()
cur.execute('SELECT transcription_text FROM transcription_history ORDER BY id DESC LIMIT 1')
row = cur.fetchone()
print(row[0] if row else '')
conn.close()
"
}

if [ -f "$LOCKFILE" ]; then
    # Segunda pulsación: parar grabación y procesar
    BEFORE_ID=$(cat "$LOCKFILE")
    rm "$LOCKFILE"
    $HANDY --toggle-transcription

    # Esperar a que Handy termine de transcribir
    sleep 3

    # Leer última transcripción
    TEXT=$(get_last_transcription)
    CURRENT_ID=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
cur = conn.cursor()
cur.execute('SELECT id FROM transcription_history ORDER BY id DESC LIMIT 1')
row = cur.fetchone()
print(row[0] if row else 0)
conn.close()
")

    if [ -n "$TEXT" ] && [ "$CURRENT_ID" != "$BEFORE_ID" ]; then
        notify-send "🎙️ Asistente" "Procesando: $TEXT"
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        python3 "$SCRIPT_DIR/assistant.py" "$TEXT"
    else
        notify-send "🎙️ Asistente" "No se detectó transcripción nueva"
    fi
else
    # Primera pulsación: guardar ID actual y empezar a grabar
    CURRENT_ID=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
cur = conn.cursor()
cur.execute('SELECT id FROM transcription_history ORDER BY id DESC LIMIT 1')
row = cur.fetchone()
print(row[0] if row else 0)
conn.close()
")
    echo "$CURRENT_ID" > "$LOCKFILE"
    $HANDY --toggle-transcription
    notify-send "🎙️ Asistente" "Escuchando..."
fi
