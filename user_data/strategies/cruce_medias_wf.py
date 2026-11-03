from pandas import DataFrame

from freqtrade.strategy import IntParameter, IStrategy


class CruceMediasWF(IStrategy):
    """Cruce de medias con periodos optimizables, para el laboratorio de walk-forward.

    No es una estrategia rentable ni una recomendación.
    """

    INTERFACE_VERSION = 3
    timeframe = '1h'
    can_short = False
    stoploss = -0.05
    minimal_roi = {'0': 0.04}
    startup_candle_count = 150

    # Los parámetros de hyperopt no se pueden usar en populate_indicators:
    # por eso las medias se calculan en populate_entry_trend y populate_exit_trend.
    rapida = IntParameter(5, 30, default=12, space='buy', optimize=True)
    lenta = IntParameter(35, 120, default=48, space='buy', optimize=True)

    def _medias(self, dataframe: DataFrame) -> tuple:
        r = dataframe['close'].ewm(span=self.rapida.value, adjust=False).mean()
        le = dataframe['close'].ewm(span=self.lenta.value, adjust=False).mean()
        return r, le

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        r, le = self._medias(dataframe)
        cruza_arriba = (r > le) & (r.shift(1) <= le.shift(1))
        dataframe.loc[cruza_arriba & (dataframe['volume'] > 0), 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        r, le = self._medias(dataframe)
        cruza_abajo = (r < le) & (r.shift(1) >= le.shift(1))
        dataframe.loc[cruza_abajo & (dataframe['volume'] > 0), 'exit_long'] = 1
        return dataframe
