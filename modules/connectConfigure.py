import json
import os
import logging

class ConnectConfig:
    # initialize object by passing in path to config file
    # store configuration data in variable data
    def __init__(self, path_to_config, relative_to=None):
        """If relative_to is supplied, all relative paths will be recomputed to be relative to the file or directory
        supplied. This allows starting the bots from other directories than where the main is. If a directory is
        given in this field, it should end with a slash.

        In testing one may want to set relative_to to be the path to the config json, so all references are relative
        to that. An application may wish to set this to __file__ in its main, meaning a configuration file from anywhere
        could be used.

        """
        self.path_to_config = path_to_config
        self.relative_to = os.path.dirname(relative_to) if relative_to is not None else os.curdir
        self.data = {}

    def _fix_relative_path(self, json_data, path_key, filename_key=None, warn_if_absent=True):
        """Given a json file, a key for a path and an optional key for a filename, extract the path
        and potentially name, resolve and join them. If warn_if_absent, issue a warning if the file
        or path does not exist at that location"""

        path = json_data[path_key]

        # Blank values are used to ignore entry. They should probably be None instead of blank but to maintain
        # backwards compatibility the function just returns "". If it continued "" would get resolved to "."
        if path == "":
            return ""

        if filename_key is not None:
            filename = json_data[filename_key]
            path = os.path.join(path, filename)
        result = os.path.normpath(os.path.join(self.relative_to, path))

        if warn_if_absent and (not os.path.exists(result)):
            parts = [p for p in [path_key, filename_key] if p is not None]
            logging.warning("{} specified in config, but resolved path {} does not exist".format(", ".join(parts), result))
        return result


    def load_config(self):
        with open(self.path_to_config, "r") as read_file:
            data = json.load(read_file)
            self.data = data

            if 'sessionAuthPort' in data:
                self.data['apiURL'] = 'https://'+ data['apiURL'] + ':' + str(data['sessionAuthPort'])
            else:
                self.data['apiURL'] = 'https://'+ data['apiURL']

            if 'privateKeyName' in data:
                self.data['botRSAPath'] = self._fix_relative_path(data, 'privateKeyPath', 'privateKeyName')


            if 'truststorePath' in data:
                self.data['truststorePath'] = self._fix_relative_path(data, 'truststorePath')


            if 'proxyURL' not in data or not data['proxyURL']:
                self.data['proxyRequestObject'] = {}
                self.data['proxyURL'] = ""
            else:
                self.data['proxyURL'] = data['proxyURL']

                if 'proxyUsername' in data and data['proxyUsername']:
                    self.data['proxyUsername'] = data['proxyUsername']
                    self.data['proxyPassword'] = data['proxyPassword']
                    pod_proxy_parse = data['proxyURL'].split('://')
                    pod_proxy_auth = data['proxyUsername'] + ':' + data['proxyPassword']
                    pod_proxy_url = pod_proxy_parse[0] + '://' + pod_proxy_auth + '@' + pod_proxy_parse[1]
                    self.data['proxyRequestObject'] = {
                            'http' : pod_proxy_url,
                            'https' : pod_proxy_url,
                            }
                else:
                    self.data['proxyRequestObject'] = {
                            'http' : data['proxyURL'],
                            'https' : data['proxyURL'],
                            }

