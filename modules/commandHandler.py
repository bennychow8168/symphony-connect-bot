import logging


class CommandHandler:

    def __init__(self, bot_client, connect_client):
        self.bot_client = bot_client
        self.connect_client = connect_client

    def command_router(self, stream_id, commandName, msg_text, msg_initiator):
        # msg_text = ['@ConnectBot', '/connect', 'wechat', 'Chung;Yeoh;chung.yeoh@symphony.com;+6597979797;RoomName']
        # msg_initiator = {'userId': 351775001412105, 'firstName': 'Chung', 'lastName': 'Yeoh', 'displayName': 'Chung Yeoh [PSDEV]', 'email': 'chung.yeoh@symphony.com', 'username': 'chung.yeoh@symphony.com'}

        # Onboard new connect user with requestor
        if commandName == '/connect':
            if len(msg_text) >= 4:
                externalNetwork = msg_text[2].upper().rstrip()

                if externalNetwork not in ("WECHAT", "WHATSAPP"):
                    msg_to_send = dict(message=f'''<messageML>ERROR: Invalid Connect Network provided. Expect "WECHAT" or "WHATSAPP" only</messageML>''')
                    self.bot_client.get_message_client().send_msg(stream_id, msg_to_send)
                    return

                # Get command parameters as whole text
                command_param_text = ' '.join(msg_text[3:])
                user_info_raw = command_param_text.split(';')

                # Parse user info
                if len(user_info_raw) >= 5:
                    contact_firstName = user_info_raw[0].rstrip()
                    contact_lastName = user_info_raw[1].rstrip()
                    contact_email = user_info_raw[2].rstrip()
                    contact_phone = user_info_raw[3].rstrip()
                    contact_company = user_info_raw[4].rstrip()
                    connect_roomName = ''

                    # Optional room name
                    if len(user_info_raw) >= 6:
                        connect_roomName = user_info_raw[5].rstrip()

                    # Connect with new member
                    msg_to_send = self.find_and_add_contact(externalNetwork, contact_firstName, contact_lastName, contact_email, contact_phone, contact_company, msg_initiator)
                    self.bot_client.get_message_client().send_msg(stream_id, msg_to_send)

                    # Add contact to Room
                    if connect_roomName != '':
                        msg_to_send = self.add_contact_to_room(externalNetwork, connect_roomName, contact_email, msg_initiator)
                        self.bot_client.get_message_client().send_msg(stream_id, msg_to_send)

                else:
                    msg_to_send = dict(message=f'''<messageML>ERROR: Insufficient Connect User Info Provided. Please refer to /help</messageML>''')
                    self.bot_client.get_message_client().send_msg(stream_id, msg_to_send)
                    return
            else:
                msg_to_send = dict(message=f'''<messageML>ERROR: Insufficient Details Provided. Please refer to /help</messageML>''')
                self.bot_client.get_message_client().send_msg(stream_id, msg_to_send)
                return

        ###########################
        # Request for an Element Form
        # @bot /connectform
        ############################
        elif commandName == '/connectform':
            self.bot_client.get_message_client().send_msg(stream_id, self.print_connect_form())
            return

        ###########################
        # Get Help
        # @bot /help
        ############################
        elif commandName == '/help':
            self.bot_client.get_message_client().send_msg(stream_id, self.print_help())
            return


    def add_contact_to_room(self, externalNetwork, roomName, contact_email, msg_initiator):
        stream_id = None
        # Get list of rooms by advisor
        status, result = self.connect_client.list_room_by_advisor(externalNetwork, msg_initiator['email'])
        if status == 'OK':
            if 'rooms' in result and len(result['rooms']) > 0:
                for r in result['rooms']:
                    if r['roomName'] == roomName:
                        print('Existing room found')
                        stream_id = r['streamId']
                        break
        else:
            msg_to_send = dict(message=f'''<messageML>Error getting list of rooms - {result}</messageML>''')
            return msg_to_send

        # Create room is necessary
        if stream_id is None:
            status, result = self.connect_client.create_room(externalNetwork, roomName, msg_initiator['email'])
            if status == 'OK':
                stream_id = result['streamId']
            else:
                msg_to_send = dict(message=f'''<messageML>Error creating new room - {result}</messageML>''')
                return msg_to_send

        # Add member to room
        if stream_id is not None:
            status, result = self.connect_client.add_room_member(externalNetwork, stream_id, contact_email, msg_initiator['email'])
            if status == 'OK':
                msg_to_send = dict(message=f'''<messageML>Successfully added {contact_email} to Room - {roomName}!</messageML>''')
                return msg_to_send
            else:
                msg_to_send = dict(message=f'''<messageML>Error adding contact to room - {result}</messageML>''')
                return msg_to_send


    def find_and_add_contact(self, externalNetwork, contact_firstName, contact_lastName, contact_email, contact_phone, contact_company, msg_initiator):
        # Get list of contacts by msg initiator
        status, result = self.connect_client.find_contacts_by_advisor(externalNetwork, msg_initiator['email'])
        if status == 'OK':
            if 'contacts' in result and len(result['contacts']) > 0:
                for c in result['contacts']:
                    if c['status'] == 'CONFIRMED' and c['emailAddress'] == contact_email:
                        msg_to_send = dict(message=f'''<messageML>{contact_email} is already an existing contact!</messageML>''')
                        return msg_to_send
                    elif c['status'] != 'CONFIRMED' and c['emailAddress'] == contact_email:
                        msg_to_send = dict(message=f'''<messageML>{contact_email} is already an existing contact, but status is {c["status"]}</messageML>''')
                        return msg_to_send
        else:
            msg_to_send = dict(message=f'''<messageML>Error getting list of contacts - {result}</messageML>''')
            return msg_to_send

        # Contact not found, try to add new contact
        status, result = self.connect_client.add_contact(externalNetwork, contact_firstName, contact_lastName, contact_email, contact_phone, contact_company, msg_initiator['email'])
        if status == 'OK':
            msg_to_send = dict(message=f'''<messageML>Successfully onboarded {contact_firstName} {contact_lastName} as a new contact!</messageML>''')
            return msg_to_send
        else:
            msg_to_send = dict(message=f'''<messageML>Error adding new contact - {result}</messageML>''')
            return msg_to_send


    def print_connect_form(self):
        output = f'''<messageML><br/><h2>Add new Connect contact</h2>
                    <br/>
                    <form id="add-connect-contact">
                    <h5>Connect Network</h5><br/>
                    <select name="externalNetwork" required="true">
                        <option value="WECHAT" selected="true">WeChat</option>
                        <option value="WHATSAPP">WhatsApp</option>
                    </select>
                    <h5>Contact First Name:</h5>
                    <text-field name="firstName" required="true"/>
                    <br/>
                    <h5>Contact Last Name:</h5>
                    <text-field name="lastName" required="true"/>
                    <br/>
                    <h5>Contact Email Address:</h5>
                    <text-field name="email" required="true"/>
                    <br/>
                    <h5>Contact Mobile Number:</h5>
                    <text-field name="mobile" required="true"/>
                    <br/>
                    <h5>Contact Company Name:</h5>
                    <text-field name="companyName" required="true"/>
                    <br/>
                    <h5>Room Name (Optional):</h5>
                    <p>Room Name to be added. New room will be created if not found</p>
                    <text-field name="roomName"/>
                    <br/>
                    <button name="connect_add" type="action">Add</button>
                    <button type="reset">Reset</button>
                    </form></messageML>'''
        output = dict(message=output)
        return output

    def print_help(self):
        output = f'''<messageML><h2>Welcome to Symphony Connect Bot!</h2><br/>
                        <table style='border-collapse:collapse;border-spacing:0px;white-space:nowrap'>
                              <tr class="tempo-text-color--black">
                                <td style='border-bottom-style:none;background-color:#b7b7b7ff;width:100px'><b>Command</b></td>
                                <td style='border-bottom-style:none;background-color:#b7b7b7ff;width:300px'><b>Usage</b></td>
                                <td style='border-bottom-style:none;background-color:#b7b7b7ff'><b>Description</b></td>
                              </tr>
                              <tr>
                                <td><b>/connect</b></td>
                                <td><b>Add New Contact</b><br/>@ConnectBot /connect [WECHAT|WHATSAPP] [FirstName;LastName;EmailAddress;MobileNumber;CompanyName]<br/><br/>
                                <b>Add Contact to Room</b><br/>@ConnectBot /connect [WECHAT|WHATSAPP] [FirstName;LastName;EmailAddress;MobileNumber;CompanyName;RoomName]<br/><br/></td>
                                <td>Allows you to connect with a new user on WeChat / WhatsApp. You may also optionally provide a room name to add new user to an existing room or new room.<br/><br/>
                                <b>Example</b><br/>@ConnectBot /connect WECHAT John;Doe;john.doe@xyz.com;+18726582942;XYZ Corp<br/>@ConnectBot /connect WECHAT John;Doe;john.doe@xyz.com;+18726582942;XYZ Corp;XYZ Room</td>
                              </tr>
                              <tr>
                                <td><b>/connectform</b></td>
                                <td>@ConnectBot /connectform</td>
                                <td>Request for an Element form to add new contact</td>
                              </tr>
                              <tr>
                                <td><b>/help</b></td>
                                <td>@ConnectBot /help</td>
                                <td>Print this help</td>
                              </tr>
                        </table></messageML>
                    '''
        output = dict(message=output)
        return output