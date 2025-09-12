"""Messaging infrastructure for RabbitMQ with Avro serialization and simple JSON messaging"""

from polako_common.messaging.contract_validator import ContractValidator
from polako_common.messaging.rabbitmq_client import RabbitMQClient

__all__ = [
    "ContractValidator",
    "RabbitMQClient"
]
