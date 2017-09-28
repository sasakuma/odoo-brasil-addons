# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    deduced_account_id = fields.Many2one(
        'account.account.template', string=u"Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account.template', string=u"Conta de Dedução do Reembolso")
    domain = fields.Selection([('icms', 'ICMS'),
                               ('icmsst', 'ICMS ST'),
                               ('simples', 'Simples Nacional'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('icms_inter', u'Difal - Alíquota Inter'),
                               ('icms_intra', u'Difal - Alíquota Intra'),
                               ('fcp', 'FCP'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
                               ('outros', 'Outros')], string="Tipo")
    amount_type = fields.Selection(selection_add=[('icmsst', 'ICMS ST')])

    def _get_tax_vals(self, company):
        res = super(AccountTaxTemplate, self)._get_tax_vals(company)
        res['domain'] = self.domain
        res['amount_type'] = self.amount_type
        return res
