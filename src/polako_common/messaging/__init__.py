"""Messaging infrastructure for RabbitMQ with Avro serialization and simple JSON messaging"""

from contract_validator import ContractValidator
from rabbitmq_client import RabbitMQClient

__all__ = [
    "ContractValidator",
    "RabbitMQClient"
]
