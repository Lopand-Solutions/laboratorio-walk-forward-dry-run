# Laboratorio: walk-forward y dry-run

Repositorio del laboratorio de [Lopand Academy](https://academy.lopandsolutions.com/tutoriales/laboratorio-walk-forward-dry-run).
Divide el histórico en ventanas, optimiza con hyperopt en cada una y valida en la siguiente con freqtrade, junta los
resultados fuera de muestra en una tabla y compara dos semanas de dry-run con su backtest.

> Esto no es consejo de inversión. La estrategia es un ejemplo de clase, no una recomendación ni algo rentable.
> Todo corre con velas públicas y en dry-run, con `api_key` y `secret` vacíos: el bot nunca opera con dinero real.

## Qué trae

| Archivo | Para qué |
| --- | --- |
| `user_data/strategies/cruce_medias_wf.py` | La estrategia con periodos optimizables |
| `ventanas.py` | Genera las ventanas en formato `--timerange` |
| `walk_forward.sh` | Corre hyperopt y backtesting por ventana |
| `juntar.py` | Junta los resultados fuera de muestra en una tabla |
| `comparar.py` | Compara el dry-run con su backtest y marca diferencias |
| `test_laboratorio.py` y `tool/` | Pruebas de los scripts y el comprobador, sin Docker ni red |

## Ramas

- **`inicio`**: las pruebas, el comprobador y el `.gitignore`. Desde aquí escribes los cinco archivos de la lección.
- **`main`**: la solución, con los cinco archivos tal como están en la lección.

## Empieza

Este laboratorio sigue a
[Backtesting riguroso con freqtrade](https://academy.lopandsolutions.com/tutoriales/backtesting-riguroso-freqtrade):
necesitas su carpeta `ft_userdata` (con `docker-compose.yml`, `user_data/config.json` sin llaves y las velas
descargadas). Clona este repo junto a ella y copia los archivos adentro, sin pisar los tuyos:

```bash
git clone https://github.com/Lopand-Solutions/laboratorio-walk-forward-dry-run.git
cp -rn laboratorio-walk-forward-dry-run/{ventanas.py,walk_forward.sh,juntar.py,comparar.py,test_laboratorio.py,tool,user_data} ft_userdata/
cd ft_userdata
```

Sigue la lección desde el paso 1. Los scripts de Python solo usan la biblioteca estándar; freqtrade corre en Docker.

## Cómo saber si quedó

```bash
./tool/comprobar_laboratorio.sh
```

No usa Docker ni red. Corre las pruebas de los scripts (necesita `pytest`: `pip install -r requirements.txt` en un
entorno virtual), revisa que `ventanas.csv` no tenga ventanas traslapadas, que haya un backtest por ventana y que
ninguna estrategia mire el futuro con `shift(-n)`. Lo que todavía no generaste sale como pendiente. El dry-run de dos
semanas y la salida de `comparar.py` se revisan a mano.

## Requisitos

Docker, Python 3.10 o superior y la carpeta `ft_userdata` de la lección anterior. Dos semanas de calendario para el
dry-run. No hace falta ninguna llave: si alguna vez ves un campo de llave con algo escrito, bórralo.

Código libre para usar y adaptar (licencia MIT).
