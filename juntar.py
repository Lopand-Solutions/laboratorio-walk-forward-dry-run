"""Junta en una tabla los backtests fuera de muestra (uno por ventana) que dejó freqtrade.

Lee todos los backtest-result-*.zip de la carpeta y saca, por estrategia, el periodo,
operaciones, ganancia total, drawdown máximo, Sharpe y Sortino.
"""
import json
import sys
import zipfile
from pathlib import Path

carpeta = Path(sys.argv[1] if len(sys.argv) > 1 else 'user_data/backtest_results')
filas = []
for zp in sorted(carpeta.glob('backtest-result-*.zip')):
    with zipfile.ZipFile(zp) as z:
        datos = json.loads(z.read(zp.with_suffix('.json').name))
    for nombre, s in datos['strategy'].items():
        filas.append((s['backtest_start'][:10], s['backtest_end'][:10], nombre, s['total_trades'],
                      s['profit_total'] * 100, s['max_drawdown_account'] * 100, s['sharpe'], s['sortino']))

if not filas:
    sys.exit(f'No hay backtest-result-*.zip en {carpeta}')

print('| Desde | Hasta | Estrategia | Operaciones | Ganancia % | Drawdown máx. % | Sharpe | Sortino |')
print('| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |')
for f in sorted(filas):
    print(f'| {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[4]:.2f} | {f[5]:.2f} | {f[6]:.2f} | {f[7]:.2f} |')

ganancias = [f[4] for f in filas]
positivas = sum(g > 0 for g in ganancias)
print(f'\nVentanas: {len(filas)} · con ganancia: {positivas} · peor: {min(ganancias):.2f} % · '
      f'operaciones totales: {sum(f[3] for f in filas)}')
