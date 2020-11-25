# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

# --- Do not remove these libs ---
from functools import reduce
from typing import Any, Callable, Dict, List

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from skopt.space import Categorical, Dimension, Integer, Real  # noqa

from freqtrade.optimize.hyperopt_interface import IHyperOpt

# --------------------------------
# Add your lib to import here
import talib.abstract as ta  # noqa
import freqtrade.vendor.qtpylib.indicators as qtpylib

shortRangeBegin = 5
shortRangeEnd = 30
mediumRangeBegin = 35
mediumRangeEnd = 70
bbWindowBegin = 15
bbWindowEnd = 120

class SimpleHyperopt(IHyperOpt):
    """
    This is a Hyperopt template to get you started.

    More information in the documentation: https://www.freqtrade.io/en/latest/hyperopt/

    You should:
    - Add any lib you need to build your hyperopt.

    You must keep:
    - The prototypes for the methods: populate_indicators, indicator_space, buy_strategy_generator.

    The methods roi_space, generate_roi_table and stoploss_space are not required
    and are provided by default.
    However, you may override them if you need 'roi' and 'stoploss' spaces that
    differ from the defaults offered by Freqtrade.
    Sample implementation of these methods will be copied to `user_data/hyperopts` when
    creating the user-data directory using `freqtrade create-userdir --userdir user_data`,
    or is available online under the following URL:
    https://github.com/freqtrade/freqtrade/blob/develop/freqtrade/templates/sample_hyperopt_advanced.py.
    """

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
        def populate_buy_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            # When would these ever not be in params??...
            if 'trigger' in params and 'bb-window' in params:
                trigger_list = params['trigger'].split('.')
                dataframe.loc[
                    (
                        (
                                (dataframe[f"maShort({trigger_list[0]})"] > dataframe[f"maMedium({trigger_list[1]})"])
                                & (dataframe[f"maMedium({trigger_list[1]})"] > dataframe["maLong"])
                                & (dataframe['close'] > dataframe[f"bbUpperBand({params['bb-window']})"])
                                & (dataframe["rsi"] > params['rsi-value'])
                        )
                    ),
                    'buy'] = 1
            return dataframe
        return populate_buy_trend

    @staticmethod
    def populate_indicators(dataframe: DataFrame, metadata: dict) -> DataFrame:
        for short in range(shortRangeBegin, shortRangeEnd):
            dataframe[f'maShort({short})'] = ta.SMA(dataframe, timeperiod=short)

        for medium in range(mediumRangeBegin, mediumRangeEnd):
            dataframe[f'maMedium({medium})'] = ta.SMA(dataframe, timeperiod=medium)

        for window in range(bbWindowBegin, bbWindowEnd, 5):
            bollinger = qtpylib.bollinger_bands(dataframe['close'], window=window, stds=2)
            dataframe[f'bbUpperBand({window})'] = bollinger['upper']

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=60)
        dataframe['maLong'] = ta.SMA(dataframe, timeperiod=1440)

        return dataframe

    @staticmethod
    def indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching buy strategy parameters.
        """
        buyTriggerList = []
        for short in range(shortRangeBegin, shortRangeEnd):
            for medium in range(mediumRangeBegin, mediumRangeEnd):
                # The output will be (short, long)
                buyTriggerList.append(
                    f"{short}.{medium}"
                )
        bbWindowList = []
        for bbWindow in range(bbWindowBegin, bbWindowEnd, 5):
            bbWindowList.append(bbWindow)

        return [
            Integer(60, 90, name='rsi-value'),
            Categorical(buyTriggerList, name='trigger'),
            Categorical(bbWindowList, name='bb-window')
        ]
    
    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching sell strategy parameters.
        """
        buyTriggerList = []
        for short in range(shortRangeBegin, shortRangeEnd):
            for medium in range(mediumRangeBegin, mediumRangeEnd):
                # The output will be (short, long)
                buyTriggerList.append(
                    f"{short}.{medium}"
                )
        return [
            Categorical(buyTriggerList, name='sell-trigger')
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:
        def populate_sell_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            conditions = []

            if 'sell-trigger' in params:
                trigger_list = params['sell-trigger'].split('.')
                dataframe.loc[
                    (
                        (
                                dataframe[f"maShort({trigger_list[0]})"] < dataframe["maLong"]
                        )
                    ),
                    'sell'] = 1
            return dataframe

        return populate_sell_trend


    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                        (dataframe[f"maShort({shortRangeBegin})"] > dataframe[f"maMedium({mediumRangeBegin})"])
                        & (dataframe[f"maMedium({mediumRangeBegin})"] > dataframe["maLong"])
                        & (dataframe['close'] > dataframe[f'bbUpperBand({bbWindowBegin})'])  # pointed up
                        & (dataframe['rsi'] > 60)
                )
            ),
            'buy'] = 1
        return dataframe


    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                        dataframe[f"maShort({shortRangeBegin})"] < dataframe["maLong"]
                )
            ),
            'sell'] = 1
        return dataframe