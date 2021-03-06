# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestElectronicInvoice(TransactionCase):

    def setUp(self):
        super(TestElectronicInvoice, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')

        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })

        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })

        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })

        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0
        })

        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'type': 'service',
            'fiscal_type': 'service',
            'list_price': 50.0
        })

        self.partner_fisica = self.env['res.partner'].create({
            'name': 'Parceiro',
            'company_type': 'company',
            'is_company': True,
            'property_account_receivable_id': self.receivable_account.id,
        })

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })

        payment_term = self.env.ref('account.account_payment_term_net')

        invoice_line_incomplete = [
            (0, 0,
             {
                 'product_id': self.default_product.id,
                 'quantity': 10.0,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
             }
             ),
            (0, 0,
             {
                 'product_id': self.service.id,
                 'quantity': 10.0,
                 'account_id': self.revenue_account.id,
                 'name': 'product test 5',
                 'price_unit': 100.00,
                 'product_type': self.service.fiscal_type,
             }
             )
        ]

        self.inv_incomplete = self.env['account.invoice'].create({
            'name': 'Teste Validação',
            'reference_type': 'none',
            'fiscal_document_id': self.env.ref(
                'br_data_account.fiscal_document_55').id,
            'journal_id': self.journalrec.id,
            'partner_id': self.partner_fisica.id,
            'account_id': self.receivable_account.id,
            'invoice_line_ids': invoice_line_incomplete,
            'payment_term_id': payment_term.id,
        })

        self.title_type = self.env.ref('br_account.account_title_type_2')
        self.financial_operation = self.env.ref(
            'br_account.account_financial_operation_6')

        # Cria parcelas
        self.inv_incomplete.generate_parcel_entry(self.financial_operation,
                                                  self.title_type)

        self.doc = self.env['invoice.electronic'].create({
            'code': '100',
            'name': 'Elec.Doc.',
        })

    def test_basic_validation_for_electronic_doc(self):
        self.assertEqual(self.inv_incomplete.total_edocs, 0)

        values = self.inv_incomplete.action_view_edocs()
        self.assertEqual(values['type'], 'ir.actions.act_window')
        self.assertEqual(values['res_model'], 'invoice.electronic')
        self.assertEqual(values['res_id'], 0)

        with self.assertRaises(UserError):
            self.inv_incomplete.action_br_account_invoice_open()

        invoice_electronic = self.env['invoice.electronic'].search(
            [('invoice_id', '=', self.inv_incomplete.id)])

        self.assertEqual(self.inv_incomplete.total_edocs, 0)
        values = self.inv_incomplete.action_view_edocs()
        self.assertEqual(values['type'], 'ir.actions.act_window')
        self.assertEqual(values['res_model'], 'invoice.electronic')
        self.assertEqual(values['res_id'], invoice_electronic.id)

    @mock.patch('odoo.fields.Date.today')
    def test_action_cancel_document(self, mk):

        mk.return_value = '2018-06-01'

        self.doc.state = 'done'

        self.doc.action_cancel_document()
        self.assertEqual(self.doc.cancel_date, '2018-06-01')
        self.assertFalse(self.doc.email_sent)

    def test_can_unlink(self):

        self.assertEqual(self.doc.state, 'draft')
        self.assertTrue(self.doc.can_unlink())

        self.doc.state = 'edit'
        self.assertFalse(self.doc.can_unlink())

        self.doc.state = 'error'
        self.assertFalse(self.doc.can_unlink())

        self.doc.state = 'done'
        self.assertFalse(self.doc.can_unlink())

        self.doc.state = 'cancel'
        self.assertFalse(self.doc.can_unlink())

    def test_unlink(self):

        with self.assertRaises(UserError):
            self.doc.state = 'edit'
            self.doc.unlink()

            self.doc.state = 'error'
            self.doc.unlink()

            self.doc.state = 'done'
            self.doc.unlink()

            self.doc.state = 'cancel'
            self.doc.unlink()

        self.doc.state = 'draft'
        self.doc.unlink()
        self.assertFalse(self.doc.exists())

    def test_action_back_to_draft(self):
        self.doc.state = 'cancel'
        self.doc.action_back_to_draft()
        self.assertEqual(self.doc.state, 'draft')

    def test_action_edit_edoc(self):
        self.doc.state = 'cancel'
        self.doc.action_edit_edoc()
        self.assertEqual(self.doc.state, 'edit')

    def test_log_exception(self):
        self.doc.log_exception('Erro')
        self.assertEqual(self.doc.codigo_retorno, '-1')
        self.assertEqual(self.doc.mensagem_retorno, 'Erro')

    def test__get_state_to_send(self):
        res = self.doc._get_state_to_send()
        self.assertIsInstance(res, tuple)
        self.assertIn('draft', res)

    def test_action_send_electronic_invoice(self):
        with self.assertRaises(UserError):
            self.doc.state = 'done'
            self.doc.action_send_electronic_invoice()
