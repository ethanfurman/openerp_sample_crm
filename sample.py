# -*- coding: utf-8 -*-

# always
from openerp.osv import fields, osv
from openerp.osv.osv import except_osv as ERPError
import logging

# often useful
from openerp import SUPERUSER_ID

# occasionally useful
import base64
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, ormcache

from fnx.oe import Proposed

_logger = logging.getLogger(__name__)

class crm_sample_request(osv.Model):
    _name = 'sample.request'
    _inherit = 'sample.request'

    def _get_tree_contacts(self, cr, uid, ids, field_names, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for sample in self.browse(cr, uid, ids, context=context):
            if sample.request_type == 'lead':
                contact = sample.lead_name or sample.lead_id.name
                company = sample.lead_company or lead_id.partner_id.name or sample.lead_id.name
                if contact in (company, None):
                    contact = False
                if company is None:
                    company = False
            elif sample.request_type == 'customer':
                contact = sample.contact_id.name
                company = sample.partner_id.name
            res[sample.id] = {'tree_contact': contact, 'tree_company': company}
        return res

    _columns = {
        'lead_name': fields.related('lead_id', 'contact_name', string='Contact', type='char', size=64),
        'lead_company': fields.related('lead_id', 'partner_name', string='Contact Company', type='char', size=64),
        # 'lead_partner_id': fields.related('lead_id', 'partner_id', string='Lead Company', type='many2one'),
        'lead_id': fields.many2one('crm.lead', 'Lead', track_visibility='onchange'),
        'partner_id': fields.many2one('res.partner', 'Company', required=False, track_visibility='onchange'),
        'request_type': fields.selection(
            [('customer', 'Customer'), ('lead', 'Lead')],
            string='Request Type', track_visibility='onchange',
            ),
        'send_to': fields.selection(
            [('rep', 'Sales Rep'), ('customer', 'Client')],
            string='Send to', required=True, track_visibility='onchange',
            ),
        'tree_contact': fields.function(
            _get_tree_contacts, type='char', size=64, multi='tree', string='Tree Contact',
            store = {'sample.request': (lambda table, cr, uid, ids, ctx=None: ids, ['contact_id', 'lead_id', 'partner_id'], 10)},
            ),
        'tree_company': fields.function(
            _get_tree_contacts, type='char', size=64, multi='tree', string='Tree Company',
            store = False,
            # store={'sample.request': (lambda table, cr, uid, ids, ctx=None: ids, ['contact_id', 'lead_id', 'partner_id'], 10)},
            ),
        }

    _defaults = {
        'request_type': 'customer',
        }

    def _get_address(
            self, cr, uid,
            send_to, user_id, contact_id, partner_id,
            request_type=False, lead_id=False, lead_company=False, lead_contact=False, context=None
            ):
        if send_to == 'rep' or request_type != 'lead':
            label = super(crm_sample_request, self)._get_address(
                    cr, uid, send_to, user_id, contact_id, partner_id, context=context,
                    )
            return label
        res = {'value': {}}
        label = []
        if lead_id:
            crm_lead = self.pool.get('crm.lead')
            lead = crm_lead.browse(cr, uid, lead_id, context=context)
            lead_partner = lead.partner_id
            csz = ''
            country = ''
            if lead.city:
                csz = lead.city
            if lead.state_id or lead.zip:
                csz += ','
                if lead.state_id:
                    csz += ' ' + lead.state_id.name
                if lead.zip:
                    csz += ' ' + lead.zip
            if lead.country_id:
                country = lead.country_id.name
            for line in (lead_contact, lead_company, lead.street, lead.street2, csz, country):
                if line:
                    label.append(line)
        label = '\n'.join(label)
        return label

    def onchange_contact_id(
            self, cr, uid, ids,
            send_to, user_id, contact_id, partner_id,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = super(crm_sample_request, self).onchange_contact_id(
                cr, uid, ids,
                send_to, user_id, contact_id, partner_id,
                context=context
                )
        if lead_id:
            del res['value']['address']
        return res

    def onchange_lead_id(
            self, cr, uid, ids,
            send_to, user_id, contact_id, partner_id,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = {'value': {}}
        if lead_id:
            crm_lead = self.pool.get('crm.lead')
            lead = crm_lead.browse(cr, uid, lead_id, context=context)
            lead_partner = lead.partner_id
            lead_company = res['value']['lead_company'] = lead.partner_name
            lead_name = res['value']['lead_name'] = lead.contact_name
            if partner_id != lead_partner.id:
                partner_id = res['value']['partner_id'] = lead_partner.id
            if contact_id:
                contact_id = res['value']['contact_id'] = False
        else:
            lead_company = res['value']['lead_company'] = False
            lead_name = res['value']['lead_name'] = False
        res['value']['address'] = self._get_address(
                cr, uid,
                send_to, user_id, contact_id, partner_id,
                request_type, lead_id, lead_company, lead_name,
                context=context
                )
        return res


    def onchange_partner_id(
            self, cr, uid, ids,
            send_to, user_id, contact_id, partner_id,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = super(crm_sample_request, self).onchange_partner_id(
                cr, uid, ids,
                send_to, user_id, contact_id, partner_id,
                context=context
                )
        if lead_id:
            del res['value']['address']
        return res

    def onchange_request_type(
            self, cr, uid, ids,
            send_to, user_id, contact_id, partner_id,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = {'value': {}}
        if request_type == 'customer':
            lead_id = res['value']['lead_id'] = False
            lead_company = res['value']['lead_company'] = False
            lead_name = res['value']['lead_name'] = False
        elif request_type == 'lead':
            contact_id = res['value']['contact_id'] = False
            partner_id = res['value']['partner_id'] = False
        res['value']['address'] = self._get_address(
                cr, uid,
                send_to, user_id, contact_id, partner_id,
                request_type, lead_id, lead_company, lead_name,
                context=context)
        return res

    def onchange_send_to(
            self, cr, uid, ids,
            send_to, user_id, contact_id, partner_id,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = {'value': {}, 'domain': {}}
        res['value']['address'] = self._get_address(
                cr, uid,
                send_to, user_id, contact_id, partner_id,
                request_type, lead_id, lead_company, lead_name,
                context=context)
        return res

    def onload(
            self, cr, uid, ids,
            send_to, user_id, contact_id, partner_id,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = {}
        if partner_id:
            res = super(crm_sample_request, self).onchange_partner_id(
                    cr, uid, ids, send_to, user_id, contact_id, partner_id,
                    context=context
                    )
            if lead_id:
                del res['value']['address']
        return res
