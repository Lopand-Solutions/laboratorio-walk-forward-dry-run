"""Genera ventanas walk-forward en el formato --timerange de freqtrade (AAAAMMDD-AAAAMMDD).

Cada ventana tiene un tramo para entrenar (hyperopt) y el tramo siguiente para validar (backtesting).
La validación nunca se traslapa con su entrenamiento, y la ventana avanza lo que dura la validación.
"""
import argparse
import csv
import sys
from datetime import date, timedelta


def fecha(texto: str) -> date:
    return date(int(texto[:4]), int(texto[4:6]), int(texto[6:8]))


def ft(d: date) -> str:
    return d.strftime('%Y%m%d')


def ventanas(inicio: date, fin: date, entrenar: int, validar: int):
    """Devuelve (n, entrenar_desde, entrenar_hasta, validar_desde, validar_hasta).

    En freqtrade, una fecha AAAAMMDD equivale a la medianoche (UTC) de ese día: el entrenamiento
    termina justo cuando empieza la validación, sin compartir velas.
    """
    n = 1
    e_desde = inicio
    while True:
        e_hasta = e_desde + timedelta(days=entrenar)
        v_hasta = e_hasta + timedelta(days=validar)
        if v_hasta > fin:
            break
        yield n, e_desde, e_hasta, e_hasta, v_hasta
        e_desde += timedelta(days=validar)
        n += 1


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inicio', required=True, help='AAAAMMDD, primer día con datos')
    p.add_argument('--fin', required=True, help='AAAAMMDD, último día con datos')
    p.add_argument('--entrenar', type=int, default=90, help='días de entrenamiento por ventana')
    p.add_argument('--validar', type=int, default=30, help='días de validación por ventana')
    a = p.parse_args()

    filas = list(ventanas(fecha(a.inicio), fecha(a.fin), a.entrenar, a.validar))
    if not filas:
        sys.exit('No cabe ni una ventana: amplía el rango o reduce los días.')
    # lineterminator: sin él, csv escribe \r\n y el \r se pega al último timerange.
    w = csv.writer(sys.stdout, lineterminator='\n')
    w.writerow(['ventana', 'entrenar', 'validar'])
    for n, ed, eh, vd, vh in filas:
        w.writerow([n, f'{ft(ed)}-{ft(eh)}', f'{ft(vd)}-{ft(vh)}'])


if __name__ == '__main__':
    main()
