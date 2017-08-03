# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Envio de NFS-e Ginfes',
    'summary': u"""Permite o envio de NFS-e através das faturas do Odoo""",
    'description': 'Envio de NFS-e - Nota Fiscal Paulistana',
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_account_einvoice',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe',
        ],
    },
    'data': [
        'data/br_nfse.xml',
        'views/br_account_service.xml',
        'views/account_invoice.xml',
        'views/invoice_eletronic.xml',
        'views/res_company.xml',
        # 'views/account_fiscal_position.xml',
        'reports/danfse_default.xml',
        'reports/nota_paulistana/danfse_sao_paulo.xml',
        'reports/simpliss/danfse_piracicaba.xml',
        'reports/ginfes/danfse_ribeirao_preto.xml',
    ],
    'installable': False,
    'application': True,
}
