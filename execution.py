import logging

class SimulatedExecution(object):
    def execute_order(self, event):
        pass

class Execution(object):
    def __init__(self, RESTaccess):
        self.RESTaccess = RESTaccess
        self.logger = logging.getLogger(__name__)

    def execute_order(self, event):
        #below is a debugger print statement so you can display the basic info of the order
        #print("start order execution " + str(event.instrument) + " " + str(event.units) + " " + str(event.side))
        status, response = self.RESTaccess.post_request_processor('/trading/open_trade', {
            'account_id': self.RESTaccess.ACCOUNT_ID,
            'symbol': event.instrument,
            'is_buy': event.side,
            'rate': 0,
            'amount': event.units,
            'at_market': 0,
            'order_type': event.order_type,
            'time_in_force': 'GTC'
        })
        if status is True:
            print('Order has been executed: {}'.format(response))
        else:
            print('Order execution error: {}'.format(response))