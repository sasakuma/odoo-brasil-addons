# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.exceptions import UserError
from odoo.addons.br_account.tests.test_base import TestBaseBr


class TestAccountInvoice(TestBaseBr):
    def setUp(self):
        super(TestAccountInvoice, self).setUp()

        self.partner_fis = self.env['res.partner'].create({
            'name': 'Nome Parceiro',
            'is_company': False,
            'property_account_receivable_id': self.receivable_account.id,
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Nome Empresa',
            'is_company': True,
            'property_account_receivable_id': self.receivable_account.id,
        })

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'update_posted': True,
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        invoice_line_data = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'quantity': 10.0,
                 'price_unit': self.default_product.list_price,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
             }
             ),
            (0, 0,
             {
                 'product_id': self.service.id,
                 'quantity': 10.0,
                 'price_unit': self.service.list_price,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'product_type': self.service.fiscal_type,
             }
             )
        ]

        payment_term = self.env.ref('account.account_payment_term_net')

        default_invoice = {
            'reference_type': "none",
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'payment_term_id': payment_term.id,
            'invoice_line_ids': invoice_line_data,
            'pre_invoice_date': '2017-07-01',
        }

        self.invoices = self.env['account.invoice'].create({
            **default_invoice,
            'name': 'Teste Fatura Pessoa Fisica',
            'partner_id': self.partner_fis.id,
        })

        self.invoices |= self.env['account.invoice'].create({
            **default_invoice,
            'name': 'Teste Fatura Empresa',
            'partner_id': self.partner.id,
        })

        # Criamos os itens da parcela da invoice
        self.title_type = self.env.ref('br_account.account_title_type_2')
        self.financial_operation = self.env.ref(
            'br_account.account_financial_operation_6')

        # Cria parcelas
        self.invoices.generate_parcel_entry(self.financial_operation,
                                            self.title_type)

    def test__compute_invoice_electronic_state(self):

        for inv in self.invoices:

            # Quando nao existe documento eletronicos na fatura
            # ela deve fica com status igual a 'no_inv_doc'
            inv._compute_invoice_electronic_state()
            self.assertEqual(inv.invoice_electronic_state, 'no_inv_doc')

            # Criamos os documentos eletronicos e as linkamos com as faturas
            docs = self.env['invoice.electronic'].create({'code': '100',
                                                          'name': 'Elec.Doc.',
                                                          'state': 'error',
                                                          'invoice_id': inv.id,
                                                          })

            docs |= self.env['invoice.electronic'].create({'code': '100',
                                                           'name': 'Elec.Doc.',
                                                           'state': 'done',
                                                           'invoice_id': inv.id,
                                                           })

            # Invocamos o metodo novamente. Desta vez ele deve retornar
            # o status do documento eletronico mais recente, ou seja, 'done'
            inv._compute_invoice_electronic_state()

            self.assertEqual(inv.invoice_electronic_state, 'done')

    @mock.patch('odoo.fields.Date.today')
    def test__compute_days_to_expire_cert(self, mk):
        
        # Mockamos a data atual para ser inferior a data de 
        # expiração do certificado.
        mk.return_value = '2018-06-01'

        for inv in self.invoices:
            inv.cert_expire_date = '2020-06-01'
            inv._compute_days_to_expire_cert()
            self.assertGreater(inv.days_to_expire_cert, 0)

        # Alteramos a data atual para ser maior que a 
        # data de expiração do certificado, fazendo o mesmo ficar
        # expirado.
        mk.return_value = '2022-06-01'
        for inv in self.invoices:
            inv._compute_days_to_expire_cert()
            self.assertLess(inv.days_to_expire_cert, 0)

    def test_action_cancel(self):

        for inv in self.invoices:

            # Criamos os documentos eletronicos e as linkamos com as faturas
            docs = self.env['invoice.electronic'].create({'code': '100',
                                                          'name': 'Elec.Doc.',
                                                          'state': 'error',
                                                          'invoice_id': inv.id,
                                                          })

            docs |= self.env['invoice.electronic'].create({'code': '100',
                                                           'name': 'Elec.Doc.',
                                                           'state': 'done',
                                                           'invoice_id': inv.id,
                                                           })

            # O cancelamento nao sera permitido porque o doc. eletronico
            # ainda nao foi cancelado
            with self.assertRaises(UserError):
                inv.action_cancel()

            # Forçamos o status de cancelado
            # no doc. que foi emitido com sucesso,
            # apenas para fins de praticidade no teste
            for doc in docs:
                if doc.state == 'done':
                    doc.state = 'cancel'

            # Como os docs ja foram nao estao mais como 'done'
            # o cancelamento funciona normalmente
            self.assertTrue(inv.action_cancel())
