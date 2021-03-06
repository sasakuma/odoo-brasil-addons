# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Pagamentos via Boleto Bancário',
    'summary': """Permite gerar e realizar a integração bancária através de
        arquivo CNAB 240 - Mantido por Trustcode""",
    'description': """Permite gerar e realizar a integração bancária através de
        arquivo CNAB 240 - Mantido por Trustcode""",
    'version': '11.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        # 'br_account_payment',
        # 'br_account_einvoice',
        # 'br_data_account_product'
    ],
    'external_dependencies': {
        'python': [
            'pyboleto',
        ],
    },
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/account_invoice.xml',
        # 'views/account_move_line.xml',
        # 'views/res_partner_bank.xml',
        # 'views/payment_order.xml',
        # 'views/payment_mode.xml',
        # 'views/account_journal.xml',
        # 'sequence/payment_order_sequence.xml',
        # 'sequence/numero_documento_sequence.xml',
        # 'wizard/br_boleto_wizard.xml',
    ],
    'installable': True,
    # 'application': True,
}
