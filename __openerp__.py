# -*- coding: utf-8 -*-

{
    'name': 'Samples: CRM Lead Integration',
    'version': '0.1',
    'category': 'Generic Modules',
    'sequence': 34,
    'summary': 'Allow Samples to be sent to Leads',
    'description': 'Allow Samples to be sent to Leads.  If Lead is converted/attached to Customer update Sample information.',
    'author': 'Van Sebille Systems',
    'depends': [
        'base',
        'sample',
        'crm',
        'fnx',
        'product',
        'web',
        ],
    'update_xml': [
        'security/sample_crm_security.xaml',
        'sample_view.xaml',
	'crm_lead_view.xaml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
