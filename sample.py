# -*- coding: utf-8 -*-

# always
from openerp.osv import fields, osv
import logging

_logger = logging.getLogger(__name__)

class crm_sample_request(osv.Model):
    _name = 'sample.request'
    _inherit = 'sample.request'
    _phone_checks = ['contact_id', 'lead_id', 'partner_id']

    def _get_tree_contacts(self, cr, uid, ids, field_names, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for sample in self.browse(cr, uid, ids, context=context):
            if sample.request_type == 'lead':
                contact = sample.lead_name or sample.lead_id.name
                company = sample.lead_company or sample.lead_id.partner_id.name or sample.lead_id.name
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
        'lead_id': fields.many2one('crm.lead', 'Lead', track_visibility='onchange', ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', 'Company', required=False, track_visibility='onchange'),
        'request_type': fields.selection(
            [('customer', 'Customer'), ('lead', 'Lead'), ('department', 'Department')],
            string='Request Type', track_visibility='onchange',
            ),
        'send_to': fields.selection(
            [('rep', 'Sales Rep'), ('customer', 'Client'), ('requester', 'Requester')],
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
        label = False
        if lead_id:
            crm_lead = self.pool.get('crm.lead')
            lead = crm_lead.browse(cr, uid, lead_id, context=context)
            label = ''
            if lead_contact:
                label += lead_contact + '\n'
            label += crm_lead._display_address(cr, uid, lead, context=context)
        return label

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = dict(super(crm_sample_request, self).name_get(cr, uid, ids, context=context))
        data = dict((r['id'], r) for r in self.read(cr, uid, ids, fields=['id', 'request_type', 'lead_id'], context=context))
        for id, name in res.items():
            data_record = data[id]
            if data_record['request_type'] == 'lead':
                name = (data_record['lead_id'] or (None, ''))[1]
                res[id] = name
        return res.items()

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
        res['value']['phone'] = self._get_phone(
                cr, uid,
                (('res.partner', contact_id), ('crm.lead', lead_id), ('res.partner', partner_id)),
                context=context,
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
        res['value']['phone'] = self._get_phone(
                cr, uid,
                (('res.partner', contact_id), ('crm.lead', lead_id), ('res.partner', partner_id)),
                context=context,
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
        res['value']['phone'] = self._get_phone(
                cr, uid,
                (('res.partner', contact_id), ('crm.lead', lead_id), ('res.partner', partner_id)),
                context=context,
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
            send_to, user_id, contact_id, partner_id, request_ship,
            request_type, lead_id, lead_company, lead_name, context=None
            ):
        res = super(crm_sample_request, self).onchange_send_to(
                cr, uid, ids, send_to, user_id, contact_id, partner_id, request_ship,
                context=context
                )
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
        res = {'value': {}, 'domain': {}}
        if partner_id:
            res = super(crm_sample_request, self).onchange_partner_id(
                    cr, uid, ids, send_to, user_id, contact_id, partner_id,
                    context=context
                    )
        if request_type == 'customer':
            partner_type_res = self.onchange_partner_type(cr, uid, ids, 0, partner_id, context=context)
            res['value'].update(partner_type_res['value'])
            res['domain'].update(partner_type_res['domain'])
        del res['value']
        return res
