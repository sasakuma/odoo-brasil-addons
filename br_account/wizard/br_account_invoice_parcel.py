# -*- coding: utf-8 -*-
# Copyright (C) 2017 MultidadosTI (http://www.multidadosti.com.br)
# @author Michell Stuttgart <michellstut@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class BrAccountInvoiceParcelWizard(models.TransientModel):
    _name = 'br_account.invoice.parcel.wizard'
    _description = 'Wizard para criar parcelas na fatura'

    payment_term_id = fields.Many2one('account.payment.term',
                                      string=u'Condições de Pagamento',
                                      readonly=True)

    pre_invoice_date = fields.Date(string='Data da Fatura',
                                   readonly=True)

    financial_operation_id = fields.Many2one('account.financial.operation',
                                             required=True,
                                             string=u'Operação Financeira')

    title_type_id = fields.Many2one('account.title.type',
                                    required=True,
                                    string=u'Tipo de Título')

    @api.multi
    def action_generate_parcel_entry(self):
        """Cria as parcelas da fatura."""

        invoices = self.env['account.invoice'].browse(
            self.env.context.get('active_ids'))

        for inv in invoices:

            inv.generate_parcel_entry(self.pre_invoice_date,
                                      self.financial_operation_id,
                                      self.title_type_id)
