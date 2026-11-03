# Pruebas de los scripts del laboratorio sin Docker, sin freqtrade y sin red. Los zip de backtest se arman aquí con
# las claves que leen juntar.py y comparar.py (las del formato de freqtrade 2026.10); los números son inventados.
import ast
import json
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

import ventanas

AQUI = Path(__file__).parent


def correr(*args, cwd=AQUI):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, capture_output=True, text=True)


def test_ventanas_da_la_tabla_de_la_leccion():
    r = correr('ventanas.py', '--inicio', '20250115', '--fin', '20260601', '--entrenar', '120', '--validar', '60')
    assert r.returncode == 0
    assert r.stdout == (
        'ventana,entrenar,validar\n'
        '1,20250115-20250515,20250515-20250714\n'
        '2,20250316-20250714,20250714-20250912\n'
        '3,20250515-20250912,20250912-20251111\n'
        '4,20250714-20251111,20251111-20260110\n'
        '5,20250912-20260110,20260110-20260311\n'
        '6,20251111-20260311,20260311-20260510\n'
    )
    assert '\r' not in r.stdout  # el \r invisible que freqtrade rechazaba


def test_entrenamiento_y_validacion_no_se_traslapan():
    for n, ed, eh, vd, vh in ventanas.ventanas(date(2025, 1, 1), date(2026, 11, 1), 90, 30):
        assert ed < eh == vd < vh <= date(2026, 11, 1)


def test_sin_espacio_para_una_ventana_sale_con_error():
    r = correr('ventanas.py', '--inicio', '20250101', '--fin', '20250201', '--entrenar', '120', '--validar', '60')
    assert r.returncode != 0 and 'No cabe ni una ventana' in r.stderr


def operacion(ratio, abs_, razon='exit_signal', abierta=False):
    return {'profit_ratio': ratio, 'profit_abs': abs_, 'exit_reason': razon, 'is_open': abierta}


def zip_de_backtest(carpeta: Path, nombre: str, inicio: str, fin: str, trades=None, ganancia=0.0155):
    carpeta.mkdir(parents=True, exist_ok=True)
    resultado = {'strategy': {'CruceMediasWF': {
        'backtest_start': f'{inicio} 00:00:00', 'backtest_end': f'{fin} 00:00:00',
        'total_trades': len(trades or []) or 30, 'profit_total': ganancia, 'max_drawdown_account': 0.0098,
        'sharpe': 1.76, 'sortino': 4.32, 'trades': trades or [],
    }}}
    ruta = carpeta / f'{nombre}.zip'
    with zipfile.ZipFile(ruta, 'w') as z:
        z.writestr(f'{nombre}.json', json.dumps(resultado))
    return ruta


def test_juntar_hace_la_tabla_y_el_resumen(tmp_path):
    zip_de_backtest(tmp_path, 'backtest-result-2026-11-02_10-00-00', '2025-05-15', '2025-07-14', ganancia=0.0155)
    zip_de_backtest(tmp_path, 'backtest-result-2026-11-02_10-01-00', '2025-07-14', '2025-09-12', ganancia=-0.0284)
    r = correr('juntar.py', tmp_path)
    assert r.returncode == 0, r.stderr
    assert '| 2025-05-15 | 2025-07-14 | CruceMediasWF | 30 | 1.55 | 0.98 | 1.76 | 4.32 |' in r.stdout
    assert 'Ventanas: 2 · con ganancia: 1 · peor: -2.84 %' in r.stdout


def test_juntar_sin_zips_sale_con_error(tmp_path):
    r = correr('juntar.py', tmp_path)
    assert r.returncode != 0 and 'No hay backtest-result-*.zip' in r.stderr


def preparar_comparacion(tmp_path, dry_run, con_log=False):
    bt = [operacion(0.01, 1.0)] * 10 + [operacion(0.5, 50.0, razon='force_exit')]
    carpeta = tmp_path / 'comparacion'
    zip_de_backtest(carpeta, 'backtest-result-2026-12-15_10-00-00', '2026-12-01', '2026-12-15', trades=bt)
    (carpeta / '.last_result.json').write_text(json.dumps({'latest_backtest': 'backtest-result-2026-12-15_10-00-00.zip'}))
    texto = json.dumps(dry_run)
    if con_log:  # show-trades a veces deja líneas de registro antes del JSON
        texto = '2026-12-15 10:00:00 - freqtrade - INFO - Using DB\n' + texto
    (tmp_path / 'dry_run.json').write_text(texto)
    return correr('comparar.py', '--backtest', carpeta, '--dry-run', tmp_path / 'dry_run.json')


def test_comparar_ok_cuando_se_parecen(tmp_path):
    # La operación abierta del dry-run y el force_exit del backtest no cuentan.
    r = preparar_comparacion(tmp_path, [operacion(0.011, 1.1)] * 9 + [operacion(None, None, abierta=True)],
                             con_log=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'OK: el dry-run se parece al backtest' in r.stdout


def test_comparar_marca_diferencia(tmp_path):
    r = preparar_comparacion(tmp_path, [operacion(-0.01, -1.0)] * 5)
    assert r.returncode == 1
    assert 'el número de operaciones difiere 50% (umbral 30%)' in r.stdout
    assert 'la ganancia promedio difiere 2.00 puntos' in r.stdout


def test_comparar_sin_operaciones_no_hay_con_que_comparar(tmp_path):
    r = preparar_comparacion(tmp_path, [])
    assert r.returncode == 1 and 'no hay con qué comparar' in r.stdout


def test_walk_forward_sh_tiene_sintaxis_valida():
    assert subprocess.run(['bash', '-n', AQUI / 'walk_forward.sh']).returncode == 0


def test_la_estrategia_compila_y_no_usa_parametros_en_populate_indicators():
    # Sin freqtrade instalado no se puede importar: se revisa el código.
    arbol = ast.parse((AQUI / 'user_data/strategies/cruce_medias_wf.py').read_text(encoding='utf-8'))
    indicadores = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == 'populate_indicators')
    assert 'self.rapida' not in ast.unparse(indicadores) and 'self.lenta' not in ast.unparse(indicadores)
    assert 'shift(-' not in ast.unparse(arbol)  # sin look-ahead


@pytest.mark.parametrize('archivo', ['ventanas.py', 'juntar.py', 'comparar.py'])
def test_solo_biblioteca_estandar(archivo):
    modulos = set()
    for n in ast.walk(ast.parse((AQUI / archivo).read_text(encoding='utf-8'))):
        if isinstance(n, ast.Import):
            modulos |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            modulos.add(n.module.split('.')[0])
    assert modulos <= set(sys.stdlib_module_names)
