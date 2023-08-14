from BodoquePi import BodoqueSystem
from utils.utils import logger_info

if __name__ == '__main__':
    logger_info.info('Starting Smartlagoon camera video processor...')
    Bodoque = BodoqueSystem()
    Bodoque.run()