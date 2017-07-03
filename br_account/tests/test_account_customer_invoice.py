# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Baseado na classe TestAccountCustomerInvoice do modulo account

from odoo.addons.account.tests.test_account_customer_invoice import \
    TestAccountCustomerInvoice
import datetime


class BrAccountTestAccountCustomerInvoice(TestAccountCustomerInvoice):
    def test_customer_invoice(self):
        # Sobrescrevemos o metodo a fim de testar a criacao de faturas com
        # o sistema de parcelas

        # I will create bank detail with using manager access rights
        # because account manager can only create bank details.
        # values = {
        #     'acc_type': 'bank',
        #     'company_id': self.main_company.id,
        #     'partner_id': self.main_partner.id,
        #     'acc_number': '123456789',
        #     'bank_id': self.main_bank.id,
        # }

        # res_partner_bank_0 = self.env['res.partner.bank'].sudo(
        #     self.account_manager.id).create(values)

        # Test with that user which have rights to make Invoicing and payment
        # and who is accountant. Create a customer invoice
        account_invoice_obj = self.env['account.invoice']

        payment_term = \
            self.env.ref('account.account_payment_term_advance')

        journalrec = \
            self.env['account.journal'].search([('type', '=', 'sale')])[0]

        partner3 = self.env.ref('base.res_partner_3')

        account_user_type = \
            self.env.ref('account.data_account_type_receivable')

        account_type_id = \
            self.env.ref('account.data_account_type_current_assets').id
        ova_search = [('user_type_id', '=', account_type_id)]
        ova = self.env['account.account'].search(ova_search, limit=1)

        account_rec1_id_vals = {
            'code': "cust_acc",
            'name': "customer account",
            'user_type_id': account_user_type.id,
            'reconcile': True,

        }

        # only adviser can create an account
        account_rec1_id = self.account_model.sudo(
            self.account_manager.id).create(account_rec1_id_vals)

        acc_search = [('user_type_id', '=',
                       self.env.ref('account.data_account_type_revenue').id)]

        account = self.env['account.account'].search(acc_search, limit=1)

        invoice_line_data = {
            'product_id': self.env.ref('product.product_product_5').id,
            'quantity': 10.0,
            'account_id': account.id,
            'name': 'product test 5',
            'price_unit': 100.00,
        }

        invoice_cust_value = {
            'name': 'Test Customer Invoice',
            'reference_type': 'none',
            'payment_term_id': payment_term.id,
            'journal_id': journalrec.id,
            'partner_id': partner3.id,
            'account_id': account_rec1_id.id,
            'invoice_line_ids': [(0, 0, invoice_line_data)]
        }

        account_invoice_customer0 = account_invoice_obj.sudo(
            self.account_user.id).create(invoice_cust_value)

        invoice = account_invoice_customer0

        # I manually assign tax on invoice
        invoice_tax_line = {
            'name': 'Test Tax for Customer Invoice',
            'manual': 1,
            'amount': 9050,
            'account_id': ova.id,
            'invoice_id': account_invoice_customer0.id,
        }
        tax = self.env['account.invoice.tax'].create(invoice_tax_line)
        assert tax, 'Tax has not been assigned correctly'

        # Criamos as parcelas da invoice
        title_type_id = self.env.ref('br_account.account_title_type_2').id
        financial_operation_id = \
            self.env.ref('br_account.account_financial_operation_6').id

        values = {
            'payment_term_id': invoice.payment_term_id.id,
            'date_invoice': invoice.date_invoice,
            'financial_operation_id': financial_operation_id,
            'title_type_id': title_type_id,
        }

        wiz = self.env['br_account.invoice.parcel.wizard'].create(values)

        wiz.with_context(
            active_ids=[invoice.id]).action_generate_parcel_entry()

        total_before_confirm = partner3.total_invoiced

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(account_invoice_customer0.state, 'draft')

        # I change the state of invoice to "Proforma2" by clicking PRO-FORMA
        # button
        account_invoice_customer0.action_invoice_proforma2()

        # I check that the invoice state is now "Proforma2"
        self.assertEquals(account_invoice_customer0.state, 'proforma2')

        # I check that there is no move attached to the invoice
        self.assertEquals(len(account_invoice_customer0.move_id), 0)

        # I validate invoice by creating on
        account_invoice_customer0.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(account_invoice_customer0.state, 'open')

        # I check that now there is a move attached to the invoice
        assert account_invoice_customer0.move_id, \
            'Move not created for open invoice'

        # I totally pay the Invoice
        journal_bank = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        account_invoice_customer0.pay_and_reconcile(journal_bank, 10050.0)

        # I verify that invoice is now in Paid state
        assert (account_invoice_customer0.state == 'paid'), \
            'Invoice is not in Paid state'

        total_after_confirm = partner3.total_invoiced
        self.assertEquals(total_after_confirm - total_before_confirm,
                          account_invoice_customer0.amount_untaxed_signed)

        # I refund the invoice Using Refund Button
        invoice_refund_obj = self.env['account.invoice.refund']
        account_invoice_refund_0 = invoice_refund_obj.create(dict(
            description='Refund To China Export',
            date=datetime.date.today(),
            filter_refund='refund'
        ))

        # I clicked on refund button.
        account_invoice_refund_0.invoice_refund()
