import logging
import sys
from modules.connectApiClient import ConnectApiClient
from modules.connectConfigure import ConnectConfig
from sym_api_client_python.configure.configure import SymConfig
from sym_api_client_python.auth.rsa_auth import SymBotRSAAuth
from sym_api_client_python.clients.sym_bot_client import SymBotClient
from listeners.im_listener_imp import IMListenerImp
from listeners.room_listener_imp import RoomListenerImp
from listeners.element_listener_imp import ElementsListenerImp


def configure_logging():
    log_level = 'DEBUG'

    logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=log_level,
            stream=sys.stdout
    )

    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stderr_handler)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def main():
    print('Starting Bot')

    # Configure log
    configure_logging()

    configure = SymConfig('./resources/bot_config.json')
    configure.load_config()

    # Init Conenct API Client
    connect_config = ConnectConfig('./resources/connect_config.json')
    connect_config.load_config()
    connect_client = ConnectApiClient(connect_config)

    auth = SymBotRSAAuth(configure)
    logging.info('Start Authenticating..')
    auth.authenticate()

    # Initialize SymBotClient with auth and configure objects
    bot_client = SymBotClient(auth, configure)

    # Initialize datafeed service
    datafeed_event_service = bot_client.get_datafeed_event_service()

    # Initialize listener objects and append them to datafeed_event_service
    # Datafeed_event_service polls the datafeed and the event listeners
    # respond to the respective types of events
    im_listener_test = IMListenerImp(bot_client, connect_client)
    datafeed_event_service.add_im_listener(im_listener_test)
    room_listener_test = RoomListenerImp(bot_client, connect_client)
    datafeed_event_service.add_room_listener(room_listener_test)
    element_listener_test = ElementsListenerImp(bot_client, connect_client)
    datafeed_event_service.add_elements_listener(element_listener_test)

    # Create and read the datafeed
    logging.info('Starting datafeed')
    datafeed_event_service.start_datafeed()
    logging.info('Datafeed Service Terminated')


if __name__ == "__main__":
    main()