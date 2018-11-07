import requests

class RESTaccessor(object):
    def __init__(self,ACCOUNT_ID,TRADING_API_URL,WEBSOCKET_PORT,ACCESS_TOKEN):
        self.ACCOUNT_ID = ACCOUNT_ID
        self.TRADING_API_URL = TRADING_API_URL
        self.WEBSOCKET_PORT = WEBSOCKET_PORT
        self.ACCESS_TOKEN = ACCESS_TOKEN
        self.bearer_access_token = ""
        self.socketIO = None

    #SocketIO definitions
    def on_error(self, ws, error):
        print(error)

    def on_close(self):
        print('Websocket closed.')

    def on_connect(self):
        print('Websocket connected: ' + self.socketIO._engineIO_session.id)
    # End of SocketIO definitions

    def create_bearer_token(self, t, s):
        bt = "Bearer " + s + t
        return bt

    def request_processor(self, method, params):
        """ Trading server request help function. """

        headers = {
            'User-Agent': 'request',
            'Authorization': self.bearer_access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        rresp = requests.get(self.TRADING_API_URL + method, headers=headers, params=params)
        if rresp.status_code == 200:
            data = rresp.json()
            if data["response"]["executed"] is True:
                return True, data
            return False, data["response"]["error"]
        else:
            return False, rresp.status_code

    def post_request_processor(self, method, params):
        """ Trading server request help function. """

        headers = {
            'User-Agent': 'request',
            'Authorization': self.bearer_access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        rresp = requests.post(self.TRADING_API_URL + method, headers=headers, data=params)
        if rresp.status_code == 200:
            data = rresp.json()
            if data["response"]["executed"] is True:
                return True, data
            return False, data["response"]["error"]
        else:
            return False, rresp.status_code
