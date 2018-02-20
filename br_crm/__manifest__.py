# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization CRM',
    'description': 'Brazilian Localization for CRM module',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://www.trustcode.com.br',
    'version': '11.0.1.0.0',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Michell Stuttgart <michellstut@gmail.com>',
    ],
    'depends': [
        'br_base',
        'crm',
    ],
    'data': [
        'views/crm_lead.xml',
        'views/crm_opportunity.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
