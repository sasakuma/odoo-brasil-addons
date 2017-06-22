# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Baseado na classe TestReconciliation do modulo account

from odoo.addons.account.tests.test_reconciliation import TestReconciliation
import time


class BrAccountTestReconciliation(TestReconciliation):
    """Tests for reconciliation (account.tax)

    Test used to check that when doing a sale or purchase invoice in a
    different currency,
    the result will be balanced.
    """

    def create_invoice(self, type='out_invoice', invoice_amount=50,
                       currency_id=None):
        # Sobrescrevemos o metodos para testarmos a funcionalidade com o
        # o sistema de parcelas

        # we create an invoice in given currency

        values = {
            'partner_id': self.partner_agrolait_id,
            'reference_type': 'none',
            'currency_id': currency_id,
            'name':
                type == 'out_invoice'
                and 'invoice to client' or 'invoice to vendor',
            'account_id': self.account_rcv.id,
            'type': type,
            'date_invoice': time.strftime('%Y') + '-07-01',
        }

        invoice = self.account_invoice_model.create(values)

        # Criamos as invoice lines

        account_type_id = self.env.ref('account.data_account_type_revenue').id
        account_id_domain = [('user_type_id', '=', account_type_id)]

        account_id = self.env['account.account'].search(account_id_domain,
                                                        limit=1).id

        line_values = {
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': invoice_amount,
            'invoice_id': invoice.id,
            'name': 'product that cost ' + str(invoice_amount),
            'account_id': account_id,
        }

        self.account_invoice_line_model.create(line_values)

        # Criamos as parcelas da invoice para que seja possivel criar um
        # lancamento de diario balanceado
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

        # validate invoice
        invoice.action_invoice_open()
        return invoice
