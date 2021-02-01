from sym_api_client_python.processors.sym_message_parser import SymMessageParser
from sym_api_client_python.processors.sym_elements_parser import SymElementsParser
from sym_api_client_python.clients.stream_client import StreamClient
from modules.commandHandler import CommandHandler
import logging, re

class MessageProcessor:
    def __init__(self, bot_client, connect_client):
        self.bot_client = bot_client
        self.message_parser = SymMessageParser()
        self.element_parser = SymElementsParser()
        self.stream_client = StreamClient(bot_client)
        self.command_handle = CommandHandler(bot_client, connect_client)


    def element_process(self, action):
        logging.debug('inside of element process')
        commandName = self.element_parser.get_form_values(action)['action']
        logging.debug(commandName)
        stream_id = self.element_parser.get_stream_id(action)
        msg_initiator = action['initiator']['user']

        ###########################
        # Connect
        # @bot /connect
        ############################
        if re.match('connect_', commandName):
            formValues = self.element_parser.get_form_values(action)
            bot_name = '@' + self.bot_client.get_bot_user_info()['displayName']
            commandName = '/connect'
            externalNetwork = formValues['externalNetwork']
            user_info_raw = f"{formValues['firstName']};{formValues['lastName']};{formValues['email']};{formValues['mobile']};{formValues['companyName']}"

            # Check Room Name
            if formValues['roomName'] != '':
                user_info_raw = user_info_raw + ";" + formValues['roomName']

            # Build msg_text
            msg_text = [bot_name]
            msg_text.append(commandName)
            msg_text.append(externalNetwork)
            msg_text.append(user_info_raw)

            self.command_handle.command_router(stream_id, commandName, msg_text, msg_initiator)
            return

        ###########################
        # Delete Contact
        ############################
        if re.match('delcontact_', commandName):
            input_param = re.search(r'(delcontact_)(.+)', commandName).group(2).split("_")
            if len(input_param) != 2:
                msg_to_send = dict(
                    message=f'''<messageML>ERROR: Unable to locate contact to delete</messageML>''')
                self.bot_client.get_message_client().send_msg(stream_id, msg_to_send)
                return

            # Build msg_text
            commandName = '/deletecontact'
            bot_name = '@' + self.bot_client.get_bot_user_info()['displayName']
            msg_text = [bot_name]
            msg_text.append(commandName)
            msg_text.append(input_param[0])
            msg_text.append(input_param[1])

            self.command_handle.command_router(stream_id, commandName, msg_text, msg_initiator)
            return


    def process(self, msg):
        logging.debug('inside of msg process')
        msg_text = self.message_parser.get_text(msg)
        stream_id = self.message_parser.get_stream_id(msg)
        stream_type = self.stream_client.stream_info_v2(stream_id)['streamType']['type']

        # Only Process if bot is mentioned:
        if msg_text and (self.isBotMentioned(msg) or stream_type == 'IM'):
            msg_initiator = self.get_msg_initiator(msg)
            msg_text = self.add_bot_for_im(msg_text, stream_type)
            if stream_type == 'IM' and msg_text is None:
                return

            if len(msg_text) > 1:
                commandName = msg_text[1].lower()
            else:
                commandName = ''

            self.command_handle.command_router(stream_id, commandName, msg_text, msg_initiator)


    def isBotMentioned(self, msg):
        mentions_list = self.message_parser.get_mentions(msg)
        bot_info = self.bot_client.get_bot_user_info()
        msg_text = self.message_parser.get_text(msg)

        if len(msg_text) > 0 and len(mentions_list) > 0:
            if msg_text[0] == mentions_list[0] and msg_text[0] == '@' + bot_info['displayName']:
                return True

        return False


    def get_msg_initiator(self, message_data):
        return message_data['user']


    def add_bot_for_im(self, msg_text, stream_type):
        bot_name = '@' + self.bot_client.get_bot_user_info()['displayName']
        if stream_type == 'IM' and len(msg_text) > 0:
            if re.match('/', msg_text[0]):
                return [bot_name] + msg_text
            elif msg_text[0] == bot_name:
                return msg_text
            else:
                return None

        return msg_text
