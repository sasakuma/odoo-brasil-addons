# -*- coding: utf-8 -*-
# © 2011  Fabio Negrini - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization CRM Zip',
    'description': """ZIP Search Integration for Brazilian
        Localization of CRM module""",
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'Fabio Negrini - OpenERP Brasil',
    'website': 'http://www.trustcode.com.br',
    'version': '10.0.1.0.0',
    'depends': [
        'br_zip',
        'br_crm',
    ],
    'data': [
    ],
    'test': [
        'test/crm_zip_test.yml'
    ],
    'installable': False,
    'auto_install': True,
}
