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

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.pre_invoice_date:
                inv.with_context(ctx).write(
                    {'pre_invoice_date': fields.Date.context_today(self)})

            pre_invoice_date = inv.pre_invoice_date
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and
            # analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency

            total, total_currency, iml = inv.with_context(
                ctx).compute_invoice_totals(company_currency, iml)

            if inv.payment_term_id:
                lines = inv.with_context(ctx).payment_term_id.with_context(
                    currency_id=company_currency.id).compute(
                    total, pre_invoice_date)[0]

                res_amount_currency = total_currency
                ctx['date'] = pre_invoice_date

                # Removemos as parcelas adicionadas anteriormente
                inv.parcel_ids.unlink()

                for i, t in enumerate(lines):
                    if inv.currency_id != company_currency:
                        amount_currency = \
                            company_currency.with_context(ctx).compute(
                                t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0

                    if i + 1 == len(lines):
                        amount_currency += res_amount_currency

                    values = {
                        'name': str(i + 1).zfill(2),
                        'parceling_value': t[1],
                        'date_maturity': t[0],
                        'financial_operation_id':
                            self.financial_operation_id.id,
                        'title_type_id': self.title_type_id.id,
                        'company_currency_id': (diff_currency and
                                                inv.currency_id.id),
                        'invoice_id': inv.id,
                    }

                    obj = self.env['br_account.invoice.parcel'].create(values)
                    # Chamamos o onchange para que a quantidade de dias seja
                    # calculado
                    obj._onchange_date_maturity()
