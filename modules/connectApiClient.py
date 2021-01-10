import requests
import json
import datetime
import logging
from jose import jwt
from json.decoder import JSONDecodeError


class ConnectApiClient():

    def __init__(self, config):
        self.config = config


    def add_contact(self, externalNetwork, firstName, lastName, email, phoneNumber, companyName, symphonyId, symphonyEmail):
        url = '/wechatgateway/api/v1/customer/contacts'

        body = {"firstName": firstName,
                "lastName": lastName,
                "emailAddress": email,
                "phoneNumber": phoneNumber,
                "companyName": companyName,
                "externalNetwork": externalNetwork,
                "onboarderEmailAddress": symphonyEmail,
                "advisorSymphonyIds":[symphonyId],
                "advisorEmailAddresses": [symphonyEmail]}

        result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        return result


    def add_room_member(self, externalNetwork, streamId, memberEmailAddress, symphonyEmail):
        url = '/wechatgateway/api/v1/customer/rooms/members'

        body = {
            "streamId": streamId,
            "memberEmailAddress": memberEmailAddress,
            "advisorEmailAddress": symphonyEmail,
            "externalNetwork": externalNetwork,
            "contact": True
            }

        result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        return result


    def create_room(self, externalNetwork, roomName, symphonyEmail):
        url = '/wechatgateway/api/v1/customer/rooms'

        body = {
            "roomName": roomName,
            "advisorEmailAddress": symphonyEmail,
            "externalNetwork": externalNetwork
            }

        result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        return result


    def list_room(self, externalNetwork, roomName, symphonyEmail):
        url = '/wechatgateway/api/v1/customer/rooms'

        body = {
            "advisorEmailAddress": symphonyEmail,
            "externalNetwork": externalNetwork,
            "owner": False
            }

        result = self.execute_rest_call(externalNetwork, "GET", url, json=body)

        # TODO: Parse room results
        return 'b11nk4dcfg4OUQsRROnPdn___okgaFM8dA'


    def parse_result(self, apiResult):
        if apiResult is not None:
            if 'status' != 200:
                return f'ERROR: {apiResult["status"]} - {apiResult["error"]} - {apiResult["message"]}'
            else:
                return 'OK'
        else:
            return 'ERROR: No response found from API call'

    def get_session(self, externalNetwork):
        session = requests.Session()
        session.headers.update({
            'Content-Type': "application/json",
            'Authorization': "Bearer " + self.create_jwt(externalNetwork)}
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
            print(url)
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

        final_output = self.parse_result(results)
        print(final_output)
        if final_output == 'OK':
            return results
        else:
            return final_output


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