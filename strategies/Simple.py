# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class Simple(IStrategy):

    # ROI table:
    minimal_roi = {
        "0": 0.25,
        "30": 0.1,
        "75": 0.05
    }

    # Stoploss:
    stoploss = -0.1

    # Trailing stop:
    trailing_stop = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # SMA
        dataframe['sma_short'] = ta.SMA(dataframe, timeperiod=10)
        dataframe['sma_mid'] = ta.SMA(dataframe, timeperiod=50)
        dataframe['sma_long'] = ta.SMA(dataframe, timeperiod=1440)
        dataframe['sma_sell'] = ta.SMA(dataframe, timeperiod=15)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=60)

        # required for graphing
        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=120, stds=2)
        dataframe['bb_upperband'] = bollinger['upper']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                        (dataframe['sma_short'] > dataframe['sma_mid'])  # over signal
                        & (dataframe['sma_mid'] > dataframe['sma_long'])
                        & (dataframe['close'] > dataframe['bb_upperband'])  # pointed up
                        & (dataframe['rsi'] > 60)  # optional filter, need to investigate
                )
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                        (dataframe['sma_sell'] < dataframe['sma_long'])  # over signal
                )
            ),
            'sell'] = 1
        return dataframe