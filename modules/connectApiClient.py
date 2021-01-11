import requests
import json
import datetime
import logging
from jose import jwt
from json.decoder import JSONDecodeError


class ConnectApiClient():

    def __init__(self, config):
        self.config = config
        self.podId = config.data['podId']


    def add_contact(self, externalNetwork, firstName, lastName, email, phoneNumber, companyName, symphonyId):
        url = '/wechatgateway/invite/v2/send'
        contactId = ''
        body = {
            "firstName": firstName,
            "lastName": lastName,
            "emailAddress": email,
            "phoneNumber": phoneNumber,
            "companyName": companyName,
            "podId": self.podId,
            "anonymous": False,
            "advisors":[symphonyId]}

        status, result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        if status == 'OK':
            contactId = self.list_contact(externalNetwork, email)

        return contactId


    def list_contact(self, externalNetwork, contactEmail):
        url = '/wechatgateway/invite/v1/list'
        status, result = self.execute_rest_call(externalNetwork, "GET", url)

        # Find if contact already exist
        if status == 'OK' and len(result) > 0:
            for record in result:
                contact_info = record['customerInfo']

                if contact_info['userId'] is not None and contact_info['emailAddress'] == contactEmail:
                    logging.info(f'Existing Contact found for "{contactEmail}" - {contact_info["userId"]}')
                    return contact_info['userId']

        return ''
    

    def find_and_add_contact(self, externalNetwork, firstName, lastName, email, phoneNumber, companyName, symphonyId):
        contactId = self.list_contact(externalNetwork, email)

        # Contact not found, create new one
        if contactId == '':
            logging.info(f'Contact not found for "{email}", creating new contact')
            contactId = self.add_contact(externalNetwork, firstName, lastName, email, phoneNumber, companyName, symphonyId)
            if contactId != '':
                logging.info(f'New Contact created for "{email}" - {contactId}')
            else:
                logging.error(f'ERROR: Unable to create new contact')

        return contactId


    def add_room_member(self, externalNetwork, streamId, connectId):
        url = f'/wechatgateway/admin/v2/room/{streamId}/members'

        body = {
            "internalMembers": [],
            "connectMembers": [connectId]
        }

        status, result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        if status == 'OK':
            return 'OK'
        else:
            return ''


    def create_room(self, externalNetwork, roomName, symphonyId, connectId):
        url = '/wechatgateway/admin/v2/room'

        body = {
            "roomName": roomName,
            "internalMembers": [symphonyId],
            "connectMembers": [connectId]
        }

        status, result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        if status == 'OK':
            return result['streamId']
        else:
            return ''


    def activate_room(self, externalNetwork, streamId):
        url = f'/wechatgateway/admin/v2/room/{streamId}/activate'
        status, result = self.execute_rest_call(externalNetwork, "POST", url)
        if status == 'OK':
            return streamId
        else:
            return ''


    def find_and_add_member_to_room(self, externalNetwork, streamId, connectId):
        url = f'/wechatgateway/admin/v2/room/{streamId}/members'
        status, result = self.execute_rest_call(externalNetwork, "GET", url)

        # Find if member already exist
        if status == 'OK' and len(result) > 0:
            for record in result:
                if record['symphonyId'] == str(connectId) and record['status'] == 'ADDED':
                    logging.debug(f'Member found in {streamId}')
                    return streamId

            # Add new member to room
            logging.debug("Adding Connect Member to Room")
            status = self.add_room_member(externalNetwork, streamId, connectId)
            if status == 'OK':
                return streamId
            else:
                return ''


    def find_and_create_and_add_member_to_room(self, externalNetwork, roomName, symphonyId, connectId):
        url = '/wechatgateway/admin/v2/room'
        stream_id = ''

        # Get list of current rooms
        status, result = self.execute_rest_call(externalNetwork, "GET", url)

        # Find if room already exist
        if status == 'OK' and len(result) > 0:
            for record in result:
                if record['roomName'] == roomName:
                    logging.debug(f'Existing Room found for "{roomName}" - {record["streamId"]}')
                    stream_id = record["streamId"]

                    # Make sure room is active, if not activate it
                    if record['status'] != 'ACTIVE':
                        logging.debug(f'Room is not active, Re-Activating Room')
                        stream_id = self.activate_room(externalNetwork, record['streamId'])

                    # Check and add member to room
                    if stream_id != '':
                        stream_id = self.find_and_add_member_to_room(externalNetwork, stream_id, connectId)

                    return stream_id

            # Room not found, create new one
            logging.debug(f'Room not found for "{roomName}", creating new room')
            stream_id = self.create_room(externalNetwork, roomName, symphonyId, connectId)

        return stream_id


    def parse_result(self, apiResult, responseCode):
        if apiResult is not None:
            if responseCode not in (200, 204):
                errorMsg = f'ERROR:'
                if 'status' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["status"]}'
                if 'error' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["error"]}'
                if 'message' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["message"]}'
                if 'errorMessage' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["errorMessage"]}'
                if 'errorCode' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["errorCode"]}'
                return errorMsg
            else:
                return 'OK'
        else:
            return 'ERROR: No response found from API call'


    def get_session(self, externalNetwork):
        session = requests.Session()
        session.headers.update({
            'Content-Type': "application/json",
            #'Authorization': "Bearer " + self.create_jwt(externalNetwork)}
            'Authorization': "Bearer " + tmp_jwt}
        )

        session.proxies.update(self.config.data['proxyRequestObject'])
        if self.config.data["truststorePath"]:
            logging.debug("Setting truststorePath to {}".format(
                self.config.data["truststorePath"])
            )
            session.verify = self.config.data["truststorePath"]

        return session


    def execute_rest_call(self, externalNetwork, method, path, **kwargs):
        results = None
        url = self.config.data['apiURL'] + path
        session = self.get_session(externalNetwork)
        try:
            logging.debug(f'Invoke API URL: {url}')
            response = session.request(method, url, **kwargs)
        except requests.exceptions.ConnectionError as err:
            logging.error(err)
            logging.error(type(err))
            raise

        if response.status_code == 204:
            results = []
        #elif response.status_code in (200, 409, 201, 404, 400):
        else:
            try:
                results = json.loads(response.text)
            except JSONDecodeError:
                results = response.text
        # else:
        #     # Try to get the json to be used to handle the error message
        #     logging.error('Failed while invoking ' + url)
        #     logging.error('Status Code: ' + str(response.status_code))
        #     logging.error('Response: ' + response.text)
        #     raise Exception(response.text)

        final_output = self.parse_result(results, response.status_code)
        logging.debug(results)
        logging.debug(final_output)
        logging.debug(f'API Output: {final_output}')
        if response.status_code in (200, 204):
            return 'OK', results
        else:
            return 'ERROR', final_output


    def create_jwt(self, externalNetwork):
        with open(self.config.data['botRSAPath'], 'r') as f:
            content = f.readlines()
            private_key = ''.join(content)
            current_date = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            expiration_date = current_date + (5*58)

            if externalNetwork == 'WHATSAPP':
                payload = {
                    'sub': 'ces:customer:' + self.config.data['publicKeyId'],
                    'exp': expiration_date,
                    'iat': current_date
                }
            elif externalNetwork == 'WECHAT':
                payload = {
                    'sub': 'ces:customer:' + self.config.data['publicKeyId'] + ':' + self.config.data['podId'],
                    'exp': expiration_date,
                    'iat': current_date
                }

            encoded = jwt.encode(payload, private_key, algorithm='RS512')
            f.close()
            return encoded