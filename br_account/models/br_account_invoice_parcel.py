# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import api, fields, models


class BrAccountInvoiceParcel(models.Model):
    """Classe utilizada para parcelamento"""
    _name = 'br_account.invoice.parcel'
    _description = 'Classe que representa as parcelas da Fatura'

    @api.model
    def _get_currency(self):
        currency = False
        context = self._context or {}
        if context.get('default_journal_id', False):
            currency = self.env['account.journal'].browse(
                context['default_journal_id']).currency_id
        return currency

    name = fields.Char(string='Parcela')

    invoice_id = fields.Many2one(comodel_name='account.invoice',
                                 string='Invoice')

    date_maturity = fields.Date(string='Data de Vencimento',
                                required=True)

    # Guarda a antiga data de vencimento apos a fatura ser confirmada
    # isso e feito para que o metodo de calculo de _compute_amount_days
    # permaneca com o mesmo valor. Isso teve de ser feito devido ao problema
    # que o Odoo tem com campos readonly sendo alterados dentro de metodos
    # onchange
    old_date_maturity = fields.Date(string='Data de Vencimento')

    parceling_value = fields.Monetary(string='Valor',
                                      required=True,
                                      readonly=True,
                                      store=True,
                                      default=0.0,
                                      currency_field='company_currency_id')

    abs_parceling_value = fields.Monetary(string='Valor',
                                          readonly=True,
                                          compute='compute_abs_parceling_value',  # noqa
                                          currency_field='company_currency_id',
                                          help=u"Armazena o valor positivo da "
                                               u"parcela (fatura de fornecedor"
                                               u"possui parcelas com valor "
                                               u"negativo). Criado apenas para"
                                               u" fins de visualização.")

    amount_currency = fields.Monetary(string='Valor em outra moeda',
                                      help="O valor da parcela expresso "
                                           "em outra moeda opcional se houver"
                                           " uma entrada multi-moeda.")

    currency_id = fields.Many2one('res.currency',
                                  string='Currency',
                                  default=_get_currency,
                                  help="Outra moeda opcional se houver uma "
                                       "entra multi-moeda.")

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
                                 compute='compute_amount_days',
                                 readonly=True)

    @api.model
    def create(self, values):
        # Atualizamos a o valor do backup da data de vencimento
        values['old_date_maturity'] = values['date_maturity']
        parcel = super(BrAccountInvoiceParcel, self).create(values)

        # Calculamos a quantidade de dias
        parcel.compute_amount_days()
        return parcel

    @api.multi
    @api.depends('parceling_value')
    def compute_abs_parceling_value(self):
        """ Retorna o valor absoluto da parcela. Isso e feito porque a fatura
        de fornecedor exibe parcelas com valores negativos. Nao podemos alterar
        o sinal da parcela porque isso impactaria diretamente na criacao das
        move lines, entao adicionamos o campo apenas para exibir o valor
        positivo da parcela sem alterar o valor original
        """
        for rec in self:
            rec.abs_parceling_value = abs(rec.parceling_value)

    @api.multi
    @api.depends('date_maturity', 'invoice_id.pre_invoice_date')
    def compute_amount_days(self):
        """ Calcula a quantidade de dias baseado na data de vencimento
        """
        for rec in self:
            if rec.old_date_maturity:
                d2 = datetime.strptime(rec.invoice_id.pre_invoice_date,
                                       '%Y-%m-%d')
                d1 = datetime.strptime(rec.old_date_maturity, '%Y-%m-%d')
                rec.amount_days = abs((d2 - d1).days)

    @api.onchange('date_maturity')
    def onchange_date_maturity(self):
        """Armazena o valor da data de vencimento no campo de backup da data
        """
        for rec in self:
            if rec.invoice_id.state == 'draft' and rec.date_maturity:
                rec.old_date_maturity = rec.date_maturity

    @api.multi
    def update_date_maturity(self, invoice_date):
        """ Calculamos a nova data de vencimento baseado na data de validação
         da faturação ou da pŕe-fatura, caso a parcela nao esteja marcada
         como 'data fixa'.

        :param invoice_date: data da fatura ou pedido.
        """
        self.ensure_one()
        if not self.pin_date:
            d1 = datetime.strptime(invoice_date, '%Y-%m-%d')
            self.old_date_maturity = self.date_maturity
            self.date_maturity = d1 + timedelta(days=self.amount_days)
