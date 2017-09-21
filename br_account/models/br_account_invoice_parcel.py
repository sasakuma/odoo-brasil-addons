# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import api, fields, models


class BrAccountInvoiceParcel(models.Model):
    """Classe utilizada para parcelamento"""
    _name = 'br_account.invoice.parcel'
    _description = 'Classe que representa as parcelas da Fatura'

    name = fields.Char(string='Parcela')

    invoice_id = fields.Many2one(comodel_name='account.invoice',
                                 string='Invoice')

    date_maturity = fields.Date(string='Data de Vencimento',
                                required=True)

    parceling_value = fields.Monetary(string='Valor',
                                      required=True,
                                      readonly=True,
                                      store=True,
                                      default=0.0,
                                      currency_field='company_currency_id')

    company_currency_id = fields.Many2one(comodel_name='res.currency',
                                          related='invoice_id.company_id.'
                                                  'currency_id',
                                          string='Company Currency',
                                          readonly=True,
                                          help='Utility field to express '
                                               'amount currency',
                                          store=True)

    financial_operation_id = fields.Many2one('account.financial.operation',
                                             string=u'Operação Financeira')

    title_type_id = fields.Many2one('account.title.type',
                                    string=u'Tipo de Título')

    pin_date = fields.Boolean(string='Data Fixa')

    amount_days = fields.Integer(string='Quantidade de Dias',
                                 store=True,
                                 readonly=True)

    @api.onchange('date_maturity')
    def _onchange_date_maturity(self):
        # Calcula a quantidade de dias baseado na data de vencimento
        for rec in self:
            if rec.invoice_id.state == 'draft' and rec.date_maturity:
                d2 = datetime.strptime(rec.invoice_id.pre_invoice_date,
                                       '%Y-%m-%d')
                d1 = datetime.strptime(rec.date_maturity, '%Y-%m-%d')
                rec.amount_days = abs((d2 - d1).days)

    @api.multi
    def update_date_maturity(self, new_date):

        # Calculamos a nova data de vencimento baseado na data
        # de validação da faturação, caso a parcela nao esteja
        # marcada como 'data fixa'. A data da parcela também é atualizada
        if not self.pin_date:
            d1 = datetime.strptime(new_date, '%Y-%m-%d')
            self.date_maturity = d1 + timedelta(days=self.amount_days)
