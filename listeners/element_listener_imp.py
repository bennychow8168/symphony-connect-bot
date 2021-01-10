import logging, sys, traceback
from sym_api_client_python.listeners.elements_listener import ElementsActionListener
from processors.message_processor import MessageProcessor


class ElementsListenerImp(ElementsActionListener):

    def __init__(self, sym_bot_client, connect_client):
        self.bot_client = sym_bot_client
        self.msg_processor = MessageProcessor(self.bot_client, connect_client)


    def on_elements_action(self, action):
        logging.debug('elements action received')
        try:
            self.msg_processor.element_process(action)
        except Exception as ex:
            exInfo = sys.exc_info()
            logging.debug('Stack Trace: ' + ''.join(traceback.format_exception(exInfo[0], exInfo[1], exInfo[2])))
            logging.error(" ##### ERROR WHILE Processing -- Elements Action #####")

