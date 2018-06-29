# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Sale',
    'description': 'Brazilian Localization for Sale',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '11.0.1.0.0',
    'depends': [
        'sale',
        'contacts',
        'br_zip',
        'br_account',
        'br_data_account_product',
    ],
    'data': [
        'views/br_sale.xml',
        'views/br_sale_parcel.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_sale_security.xml',
        'wizard/br_sale_parcel_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
