#!/bin/bash

# 1. Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activo."
else
    echo "❌ No se encontró la carpeta venv. Ejecuta 'python -m venv venv' primero."
    exit 1
fi

# 2. Configurar Path de Python
export PYTHONPATH=$PYTHONPATH:.

# 3. Lanzar el servidor con autorecarga total
echo "🚀 Iniciando IntelliBusiness Suite..."
uvicorn app.main:app \
    --reload \
    --reload-include "*.json" \
    --reload-include "*.html" \
    --reload-include "*.css" \
    --port 8000