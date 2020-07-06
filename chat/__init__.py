import logging


log = logging.getLogger(__name__)

handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
handler.setLevel('DEBUG')
log.addHandler(handler)