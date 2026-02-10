from loguru import logger
import sys

def setup_logging():
    logger.remove()
    logger.add(sys.stdout, level="INFO", backtrace=False, diagnose=False,
               format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>")
    return logger
