# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Purchase and Warehouse',
    'description': 'Brazilian Localization Purchase and Warehouse Link',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
    'version': '11.0.1.0.0',
    'depends': [
        'br_purchase',
        'br_stock_account',
    ],
    'data': [
        'views/purchase_order.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
