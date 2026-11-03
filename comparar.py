"""Compara un backtest de freqtrade con las operaciones de un dry-run del mismo periodo.

Lee:
  - el resultado del backtest: el .zip de user_data/backtest_results (o la carpeta, y toma el último);
  - el dry-run: el JSON de `freqtrade show-trades --print-json` guardado en un archivo.
Marca DIFERENCIA cuando el número de operaciones o la ganancia promedio se separan más que el umbral.
"""
import argparse
import json
import statistics
import sys
import zipfile
from pathlib import Path


def cargar_backtest(ruta: Path, estrategia: str | None) -> list[dict]:
    if ruta.is_dir():
        # freqtrade anota el último resultado en .last_result.json
        ultimo = json.loads((ruta / '.last_result.json').read_text())['latest_backtest']
        ruta = ruta / ultimo
    with zipfile.ZipFile(ruta) as z:
        datos = json.loads(z.read(ruta.with_suffix('.json').name))
    estrategias = datos['strategy']
    if estrategia is None:
        if len(estrategias) != 1:
            sys.exit(f'El backtest tiene varias estrategias: {", ".join(estrategias)}. Usa --estrategia.')
        estrategia = next(iter(estrategias))
    return estrategias[estrategia]['trades']


def cargar_dry_run(ruta: Path) -> list[dict]:
    lineas = ruta.read_text().splitlines()
    # Por si el archivo trae líneas de log antes del JSON: empieza en la línea que abre la lista.
    inicio = next((i for i, x in enumerate(lineas) if x.lstrip().startswith('[')), None)
    if inicio is None:
        sys.exit(f'{ruta} no tiene la lista JSON de show-trades --print-json')
    return json.loads('\n'.join(lineas[inicio:]))


def resumen(operaciones: list[dict]) -> dict:
    # El backtest cierra a la fuerza (force_exit) lo que sigue abierto al final; el dry-run lo deja abierto.
    # Para comparar lo mismo, contamos solo operaciones cerradas por la estrategia.
    cerradas = [o for o in operaciones if not o.get('is_open') and o.get('exit_reason') != 'force_exit']
    ratios = [o['profit_ratio'] for o in cerradas if o.get('profit_ratio') is not None]
    return {
        'operaciones': len(cerradas),
        'ganancia_prom_pct': statistics.mean(ratios) * 100 if ratios else 0.0,
        'ganancia_total': sum(o.get('profit_abs') or 0.0 for o in cerradas),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backtest', type=Path, required=True)
    p.add_argument('--dry-run', type=Path, required=True)
    p.add_argument('--estrategia')
    p.add_argument('--umbral-operaciones', type=float, default=0.30,
                   help='diferencia relativa máxima en número de operaciones (0.30 = 30 %%)')
    p.add_argument('--umbral-ganancia', type=float, default=0.50,
                   help='diferencia máxima en ganancia promedio por operación, en puntos porcentuales')
    a = p.parse_args()

    bt = resumen(cargar_backtest(a.backtest, a.estrategia))
    dr = resumen(cargar_dry_run(a.dry_run))

    print(f"{'':22}{'Backtest':>12}{'Dry-run':>12}")
    for clave, nombre in [('operaciones', 'Operaciones cerradas'),
                          ('ganancia_prom_pct', 'Ganancia prom. (%)'),
                          ('ganancia_total', 'Ganancia total')]:
        print(f'{nombre:22}{bt[clave]:>12.2f}{dr[clave]:>12.2f}')

    problemas = []
    if bt['operaciones'] == 0 or dr['operaciones'] == 0:
        problemas.append('uno de los dos no tiene operaciones cerradas: no hay con qué comparar')
    else:
        dif_ops = abs(bt['operaciones'] - dr['operaciones']) / bt['operaciones']
        if dif_ops > a.umbral_operaciones:
            problemas.append(f'el número de operaciones difiere {dif_ops:.0%} (umbral {a.umbral_operaciones:.0%})')
        dif_g = abs(bt['ganancia_prom_pct'] - dr['ganancia_prom_pct'])
        if dif_g > a.umbral_ganancia:
            problemas.append(f'la ganancia promedio difiere {dif_g:.2f} puntos (umbral {a.umbral_ganancia:.2f})')

    if problemas:
        print('\nDIFERENCIA:')
        for x in problemas:
            print(f'  - {x}')
        return 1
    print('\nOK: el dry-run se parece al backtest dentro de los umbrales.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
