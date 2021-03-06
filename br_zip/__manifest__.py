# © 2009 Renato Lima, Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2017-2018 Michell Stuttgart, Multidados
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localisation ZIP Codes',
    'description': 'Brazilian Localization ZIP Codes',
    'license': 'AGPL-3',
    'category': 'Localization',
    'author': 'Akretion, Odoo Brasil',
    'version': '11.0.1.0.0',
    'depends': [
        'br_base',
    ],
    'external_dependencies': {
        'python': [
            'pycep_correios',
        ],
    },
    'data': [
        'views/br_zip_view.xml',
        'views/res_partner_view.xml',
        'views/res_bank_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
