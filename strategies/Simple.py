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
        "0": 0.11721,
        "37": 0.06113,
        "75": 0.03839,
        "148": 0
    }

    # Stoploss:
    stoploss = -0.30808

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.32231
    trailing_stop_positive_offset = 0.4197
    trailing_only_offset_is_reached = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # SMA
        dataframe['sma_short'] = ta.SMA(dataframe, timeperiod=8)
        dataframe['sma_mid'] = ta.SMA(dataframe, timeperiod=58)
        dataframe['sma_long'] = ta.SMA(dataframe, timeperiod=1440)
        dataframe['sma_sell'] = ta.SMA(dataframe, timeperiod=15)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=60)

        # required for graphing
        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=30, stds=2)
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