import logging

from tqdm.contrib.logging import _TqdmLoggingHandler, std_tqdm


def build_logger(debug_level=logging.DEBUG):
    # create logger
    logger = logging.getLogger("icekube")
    logger.setLevel(debug_level)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(debug_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(message)s")
    ch.setFormatter(formatter)

    # tell tqdm about the handler
    tqdm_handler = _TqdmLoggingHandler(std_tqdm)
    tqdm_handler.setFormatter(formatter)
    tqdm_handler.stream = ch.stream

    # add the handlers to the logger
    logger.addHandler(tqdm_handler)
