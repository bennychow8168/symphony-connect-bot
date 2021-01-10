import logging, sys, traceback
from sym_api_client_python.listeners.im_listener import IMListener
from processors.message_processor import MessageProcessor


# A sample implementation of Abstract imListener class
# The listener can respond to incoming events if the respective event
# handler has been implemented


class IMListenerImp(IMListener):
    """Example implementation of IMListener
        sym_bot_client: contains clients which respond to incoming events
    """

    def __init__(self, sym_bot_client, connect_client):
        self.bot_client = sym_bot_client
        self.msg_processor = MessageProcessor(self.bot_client, connect_client)

    def on_im_message(self, im_message):
        logging.debug('message received in IM')

        try:
            self.msg_processor.process(im_message)
        except Exception as ex:
            exInfo = sys.exc_info()
            logging.debug('Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
            logging.error(" ##### ERROR WHILE Processing -- IM Message #####")

    def on_im_created(self, im_created):
        logging.debug('IM created!', im_created)


