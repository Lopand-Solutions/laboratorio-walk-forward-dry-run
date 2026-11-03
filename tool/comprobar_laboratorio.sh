#!/usr/bin/env bash
# Comprueba el laboratorio «Walk-forward y dry-run». Uso, desde ft_userdata o desde el repo:
#   ./tool/comprobar_laboratorio.sh
# No usa Docker ni red: corre las pruebas de los scripts y revisa lo que ya generaste (ventanas.csv, los zip del
# walk-forward y tu estrategia). Lo que todavía no generaste sale como pendiente, no como falla.
set -uo pipefail
cd "$(dirname "$0")/.."
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi
fallas=0
bien() { printf '  ✓ %s\n' "$1"; }
mal()  { printf '  ✗ %s\n' "$1"; fallas=$((fallas + 1)); }
pend() { printf '  · %s\n' "$1"; }

echo "1. Los scripts"
if "$PY" -m pytest -q -p no:cacheprovider test_laboratorio.py >/tmp/wf-pytest.$$ 2>&1; then
  bien "pytest en verde ($(tail -1 /tmp/wf-pytest.$$))"
else
  mal "pytest en rojo: $(tail -1 /tmp/wf-pytest.$$)"
fi
rm -f /tmp/wf-pytest.$$

echo "2. Las ventanas"
if [ -f ventanas.csv ]; then
  if "$PY" - <<'PY'
import csv, sys
from datetime import date
f = lambda t: date(int(t[:4]), int(t[4:6]), int(t[6:8]))
with open('ventanas.csv', newline='') as a:
    filas = list(csv.DictReader(a))
ok = bool(filas) and all(f(r['entrenar'][:8]) < f(r['entrenar'][9:]) == f(r['validar'][:8]) < f(r['validar'][9:])
                         and '\r' not in r['validar'] for r in filas)
sys.exit(0 if ok else 1)
PY
  then bien "ventanas.csv: $(($(wc -l < ventanas.csv) - 1)) ventanas sin traslape entre entrenamiento y validación"
  else mal "ventanas.csv tiene ventanas que se traslapan o un \\r al final: genéralo otra vez con ventanas.py"; fi
else pend "todavía no hay ventanas.csv (paso 2)"; fi

echo "3. El walk-forward"
salida=user_data/backtest_results/walk-forward
if [ -d "$salida" ] && [ -f ventanas.csv ]; then
  esperadas=$(( $(wc -l < ventanas.csv) - 1 ))
  hay=$(find "$salida" -name 'backtest-result-*.zip' | wc -l)
  [ "$hay" -eq "$esperadas" ] && bien "$hay de $esperadas backtests de validación en $salida" \
    || mal "hay $hay backtests y ventanas.csv pide $esperadas: corre ./walk_forward.sh otra vez"
else pend "todavía no hay resultados del walk-forward (paso 3)"; fi

echo "4. Sin look-ahead en tus estrategias"
if grep -nE 'shift\(-[0-9]' user_data/strategies/*.py 2>/dev/null; then
  mal "una estrategia usa shift(-n): mira el futuro. Quítalo (reto)"
else bien "ninguna estrategia usa shift(-n)"; fi

echo
if [ "$fallas" -eq 0 ]; then echo "Sin fallas. El dry-run y comparar.py se revisan a mano (pasos 5 y 6)."; exit 0; fi
echo "Faltan $fallas punto(s)."; exit 1
