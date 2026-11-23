#!/usr/bin/env bash
# Сборка существ босса 5 по одному на процесс Blender (свет студии не копится), по 4 параллельно.
# Запуск из корня репозитория: bash scripts/run_glacier.sh <кадры> [quick] [id…]
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
OUT="$1"; shift
MODE=""; if [ "$1" = "quick" ]; then MODE="quick"; shift; fi
IDS="$*"
if [ -z "$IDS" ]; then
  IDS=$(python -c "import re;print(' '.join(re.findall(r'\(\"(\w+)\", \w+, \"', open('scripts/blender/art_glacier.py',encoding='utf-8').read())))")
fi
mkdir -p "$OUT/logs"
n=0
for id in $IDS; do
  ( "$B" --background --factory-startup --python scripts/blender/art_glacier.py -- . "$OUT" $MODE $id > "$OUT/logs/$id.log" 2>&1; grep -h "CREATURES_OK\|Traceback\|Error:" "$OUT/logs/$id.log" | grep -v "Shadow buffer" | head -3 | sed "s/^/$id: /" ) &
  n=$((n+1)); if [ $((n % 4)) -eq 0 ]; then wait; fi
done
wait
