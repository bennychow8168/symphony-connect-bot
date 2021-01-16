import requests
import json
import datetime
import logging
import urllib.parse
from jose import jwt
from json.decoder import JSONDecodeError


class ConnectApiClient():

    def __init__(self, config):
        self.config = config
        self.podId = config.data['podId']


    def find_advisor(self, externalNetwork, advisorEmail):
        url = f'/wechatgateway/api/v1/customer/advisors?externalNetwork={externalNetwork}&advisorEmailAddress={urllib.parse.quote_plus(advisorEmail)}'
        status, result = self.execute_rest_call(externalNetwork, "GET", url)

        return status, result


    def find_contacts_by_advisor(self, externalNetwork, advisorEmailAddress):
        url = f'/wechatgateway/api/v1/customer/advisors/advisorEmailAddress/{urllib.parse.quote_plus(advisorEmailAddress)}/externalNetwork/{externalNetwork}/contacts'
        status, result = self.execute_rest_call(externalNetwork, "GET", url)

        return status, result


    def find_advisors_by_contact(self, externalNetwork, contactEmail):
        url = f'/wechatgateway/api/v1/customer/contacts/contactEmailAddress/{urllib.parse.quote_plus(contactEmail)}/externalNetwork/{externalNetwork}/advisors'
        status, result = self.execute_rest_call(externalNetwork, "GET", url)

        return status, result


    def add_contact(self, externalNetwork, firstName, lastName, email, phoneNumber, companyName, advisorEmailAddress):
        url = '/wechatgateway/api/v1/customer/contacts'

        body = {
            "firstName": firstName,
            "lastName": lastName,
            "companyName": companyName,
            "emailAddress": email,
            "phoneNumber": phoneNumber,
            "externalNetwork": externalNetwork,
            "advisorEmailAddresses": [advisorEmailAddress],
            "onboarderEmailAddress": advisorEmailAddress
            }

        status, result = self.execute_rest_call(externalNetwork, "POST", url, json=body)

        return status, result


    def add_room_member(self, externalNetwork, streamId, contactEmail, advisorEmailAddress):
        url = f'/wechatgateway/api/v1/customer/rooms/members'

        body = {
            "streamId": streamId,
            "memberEmailAddress": contactEmail,
            "advisorEmailAddress": advisorEmailAddress,
            "externalNetwork": externalNetwork,
            "contact": True
            }

        status, result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        return status, result


    def remove_room_member(self, externalNetwork, streamId, contactEmail, advisorEmailAddress):
        url = f'/wechatgateway/api/v1/customer/rooms/{streamId}/members?memberEmailAddress={urllib.parse.quote_plus(contactEmail)}&advisorEmailAddress={urllib.parse.quote_plus(advisorEmailAddress)}&externalNetwork={externalNetwork}&contact=false'

        status, result = self.execute_rest_call(externalNetwork, "DELETE", url)
        return status, result


    def create_room(self, externalNetwork, roomName, advisorEmailAddress):
        url = '/wechatgateway/api/v1/customer/rooms'

        body = {
            "roomName": roomName,
            "advisorEmailAddress": advisorEmailAddress,
            "externalNetwork": externalNetwork
            }

        status, result = self.execute_rest_call(externalNetwork, "POST", url, json=body)
        return status, result


    def parse_result(self, apiResult, responseCode):
        if apiResult is not None:
            if responseCode not in (200, 204):
                errorMsg = f'ERROR:'
                if 'status' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["status"]}'
                if 'error' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["error"]}'
                if 'type' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["type"]}'
                if 'title' in apiResult:
                    errorMsg = errorMsg + f' - {apiResult["title"]}'
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
            logging.debug(f'Invoke API URL: {url}')
            response = session.request(method, url, **kwargs)
        except requests.exceptions.ConnectionError as err:
            logging.error(err)
            logging.error(type(err))
            raise

        if response.status_code == 204:
            results = []
        else:
            try:
                results = json.loads(response.text)
            except JSONDecodeError:
                results = response.text

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