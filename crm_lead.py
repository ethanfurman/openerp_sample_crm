from openerp.osv import osv
import logging

_logger = logging.getLogger(__name__)

## tables

class crm_lead(osv.Model):
    _name = "crm.lead"
    _inherit = 'crm.lead'

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if view_id:
            return super(crm_lead, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)
        if context is None:
            context = {}
        lead_id = view_type == 'form' and context.get('active_lead_id')
        if lead_id is not None:
            lead = self.pool.get('crm.lead').browse(cr, user, lead_id, context=context)
            if lead.type == 'opportunity':
                imd = self.pool.get('ir.model.data')
                _, view_id = imd.get_object_reference(cr, user, 'fis_integration', 'crm_case_form_view_oppor')
        return super(crm_lead, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)


