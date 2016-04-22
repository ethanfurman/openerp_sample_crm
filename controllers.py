# -*- coding: utf-8 -*-

from openerp.addons.sample import controllers
import logging

_logger = logging.getLogger(__name__)

class SampleCrmRequest(controllers.SampleRequest):

    _cp_path = '/samplerequest'

    def get_sales_left(self, order):
        if order.send_to == 'Client':
            return super(SampleCrmRequest, self).get_sales_left(order)
        main = [
                ['Department', order.department],
                ['Request by', order.user_id.name],
                ['Created on', order.create_date],
                ['Samples Must', order.target_date_type + ' by ' + order.target_date],
                ['Send to', order.send_to],
                ]
        recip = [
                ['Recipient',
                    '\n'.join([
                        t for t in
                        (order.lead_id.name_get, order.lead_company, order.lead_name)
                        if t
                        ])],
                ]
        return main + recip
