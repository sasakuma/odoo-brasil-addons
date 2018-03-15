# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Envio de NFS-e',
    'summary': """Permite o envio de NFS-e através das faturas do Odoo.""",
    'description': 'Envio de NFS-e - Nota Fiscal Paulistana',
    'version': '11.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Michell Stuttgart <michellstut@gmail.com>',
    ],
    'depends': [
        'product',
        'br_account_einvoice',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/br_nfse.xml',
        'views/br_account_service.xml',
        'views/res_company.xml',
        'views/account_invoice.xml',
        'views/invoice_electronic.xml',
        'views/account_fiscal_position.xml',
        'reports/danfse_default.xml',
        'wizard/br_account_invoice_print.xml',
    ],
    'demo': [
        'demo/product_demo.xml',
    ],
    'installable': True,
    'application': False,
}
