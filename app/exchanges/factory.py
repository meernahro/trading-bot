from typing import Optional

from ..schemas import ExchangeType, MarketType
from ..utils.exceptions import ValidationError
from .base import ExchangeClientBase
from .binance_spot import BinanceSpotClient
from .bybit_spot import BybitSpotClient
from .kucoin_spot import KuCoinSpotClient
from .mexc_spot import MEXCSpotClient
from .okx_spot import OKXSpotClient


class ExchangeClientFactory:
    """Factory class to create exchange clients"""

    @staticmethod
    def create_client(
        exchange: ExchangeType,
        market_type: MarketType,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        testnet: bool = False,
    ) -> ExchangeClientBase:
        """
        Create and return appropriate exchange client

        Args:
            exchange: Exchange type (binance, mexc, etc.)
            market_type: Market type (spot, futures)
            api_key: API key
            api_secret: API secret
            passphrase: Passphrase for KuCoin
            testnet: Whether to use testnet

        Returns:
            ExchangeClientBase: Appropriate exchange client instance

        Raises:
            ValidationError: If exchange/market combination is not supported
        """

        if exchange == ExchangeType.BINANCE:
            if market_type == MarketType.SPOT:
                return BinanceSpotClient(api_key, api_secret, testnet)
        elif exchange == ExchangeType.MEXC:
            if market_type == MarketType.SPOT:
                return MEXCSpotClient(api_key, api_secret, testnet)
        elif exchange == ExchangeType.KUCOIN:
            if not passphrase:
                raise ValidationError("Passphrase is required for KuCoin")
            if market_type == MarketType.SPOT:
                return KuCoinSpotClient(api_key, api_secret, passphrase, testnet)
        elif exchange == ExchangeType.OKX:
            if not passphrase:
                raise ValidationError("Passphrase is required for OKX")
            if market_type == MarketType.SPOT:
                return OKXSpotClient(api_key, api_secret, passphrase, testnet)
        elif exchange == ExchangeType.BYBIT:
            if market_type == MarketType.SPOT:
                return BybitSpotClient(api_key, api_secret, testnet)

        raise ValidationError(
            f"Unsupported exchange/market combination: {exchange}/{market_type}"
        )
