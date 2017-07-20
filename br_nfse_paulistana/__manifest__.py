# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI

{
    'name': 'Envio de NFS-e Paulistana',
    'summary': """Permite o envio de NFS-e Paulistana através das faturas do
     Odoo""",
    'description': 'Envio de NFS-e - Nota Fiscal Paulistana',
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'MultidadosTI',
    'license': 'AGPL-3',
    'website': 'http://www.multidadosti.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Michell Stuttgart <michellstut@gmail.com>',
    ],
    'depends': [
        'br_nfse',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe',
        ],
    },
    'data': [
        'reports/danfse_sao_paulo.xml',
        'data/br_nfse_paulistana.xml',
        'views/br_account_service.xml',
        'views/invoice_eletronic.xml',
    ],
    'installable': True,
    'application': True,
}
