#!/usr/bin/env bash
# Walk-forward: hyperopt en cada tramo de entrenamiento y backtesting en su tramo de validación.
# Cada backtest de validación queda como un .zip aparte en $SALIDA.
set -euo pipefail
FT=${FT:-"docker compose run --rm -T freqtrade"}
ESTRATEGIA=CruceMediasWF
SALIDA=user_data/backtest_results/walk-forward

# Empezamos con la carpeta vacía para que juntar.py no mezcle corridas viejas.
rm -rf "$SALIDA"
mkdir -p "$SALIDA"

# </dev/null: sin esto, docker compose run se come el resto de ventanas.csv que lee el while.
tail -n +2 ventanas.csv | while IFS=, read -r n entrenar validar; do
  echo "▶ Ventana $n: entrena $entrenar, valida $validar"
  # Los parámetros de la ventana anterior no deben contaminar esta.
  rm -f "user_data/strategies/$ESTRATEGIA.json"
  $FT hyperopt --config user_data/config.json --strategy "$ESTRATEGIA" \
    --hyperopt-loss SharpeHyperOptLoss --spaces buy -e 50 --random-state 42 \
    --timerange "$entrenar" --fee 0.001 </dev/null
  $FT backtesting --config user_data/config.json --strategy "$ESTRATEGIA" \
    --timerange "$validar" --fee 0.001 --backtest-directory "$SALIDA" </dev/null
done

# freqtrade puede terminar con código 0 aunque rechace un argumento: contamos los resultados.
esperadas=$(( $(wc -l < ventanas.csv) - 1 ))
hay=$(find "$SALIDA" -name 'backtest-result-*.zip' | wc -l)
if [ "$hay" -ne "$esperadas" ]; then
  echo "✗ Se esperaban $esperadas backtests y hay $hay. Revisa el registro de arriba." >&2
  exit 1
fi
echo "✓ $hay ventanas listas en $SALIDA"
