# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Purchase',
    'description': 'Brazilian Localization for Purchase',
    'category': 'purchase',
    'license': 'AGPL-3',
    'author': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
    'version': '11.0.1.0.0',
    'depends': [
        'purchase',
        'br_account',
    ],
    'data': [
        'views/purchase_order.xml',
        'views/purchase_views.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
