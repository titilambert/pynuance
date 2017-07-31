"""PyNuance main logger"""
import logging

_FORMAT = '%(asctime)-15s %(filename)-8s %(message)s'

logging.basicConfig(format=_FORMAT)

LOGGER_ROOT = logging.getLogger("pynuance")
