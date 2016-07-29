# -*- coding: utf-8 -*-

from openerp.addons.sample import controllers
import logging

_logger = logging.getLogger(__name__)

class SampleCrmRequest(controllers.SampleRequest):

    _cp_path = '/samplerequest'

    def get_sales_left(self, order):
        sales_left = super(SampleCrmRequest, self).get_sales_left(order)
        if order.request_type == 'Customer':
            return sales_left
        for line in sales_left:
            if line[0] == 'Recipient':
                line[1] = '\n'.join([
                            t for t in
                            (order.lead_id.name_get, order.lead_company, order.lead_name)
                            if t
                            ])
        return sales_left
