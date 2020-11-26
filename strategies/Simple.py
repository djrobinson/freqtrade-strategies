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
        "0": 0.13751,
        "22": 0.02265,
        "49": 0.01024,
        "140": 0
    }

    # Stoploss:
    stoploss = -0.27337

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.10213
    trailing_stop_positive_offset = 0.13996
    trailing_only_offset_is_reached = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # SMA
        dataframe['sma_short'] = ta.SMA(dataframe, timeperiod=29)
        dataframe['sma_mid'] = ta.SMA(dataframe, timeperiod=64)
        dataframe['sma_long'] = ta.SMA(dataframe, timeperiod=1440)
        dataframe['sma_sell'] = ta.SMA(dataframe, timeperiod=6)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=60)

        # required for graphing
        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=95, stds=2)
        dataframe['bb_upperband'] = bollinger['upper']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                        (dataframe['sma_short'] > dataframe['sma_mid'])  # over signal
                        & (dataframe['sma_mid'] > dataframe['sma_long'])
                        & (dataframe['close'] > dataframe['bb_upperband'])  # pointed up
                        & (dataframe['rsi'] > 61)  # optional filter, need to investigate
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