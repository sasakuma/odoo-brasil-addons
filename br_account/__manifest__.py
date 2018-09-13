# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Account',
    'description': """Brazilian Localization Account""",
    'version': '11.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
        'Michell Stuttgart <michellstut@gmail.com>'
    ],
    'depends': [
        'account',
        'br_base',
        'account_cancel'
    ],
    'data': [
        'data/account_financial_operation.xml',
        'data/account_title_type.xml',
        'data/br_nfs.xml',
        'views/account_financial_operation.xml',
        'views/account_title_type.xml',
        'views/account_fiscal_position.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/account_payment.xml',
        'views/account_account.xml',
        'views/br_account.xml',
        'views/br_account_cfop.xml',
        'views/br_account_cnae.xml',
        'views/br_account_document_serie.xml',
        'views/br_account_fiscal_document.xml',
        'views/br_account_fiscal_observation.xml',
        'views/br_account_import_declaration_line.xml',
        'views/br_account_invoice_parcel.xml',
        'views/br_account_service_type.xml',
        'views/product_template.xml',
        'views/res_company.xml',
        'views/account_tax.xml',
        'views/res_partner.xml',
        'views/product_fiscal_classification.xml',
        'views/product_pricelist_views.xml',
        'wizard/account_invoice_confirm.xml',
        'wizard/br_account_invoice_print.xml',
        'wizard/br_product_fiscal_classification_wizard.xml',
        'wizard/br_account_invoice_parcel.xml',
        'security/account_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/res_partner.xml',
        'demo/product_fiscal_classification.xml',
        'demo/product_template.xml',
    ],
    'installable': True,
}
