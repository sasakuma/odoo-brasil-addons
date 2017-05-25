# -*- coding: utf-8 -*-

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class AccountTitleType(models.Model):
    _name = 'account.title.type'

    @api.model
    def _default_company_currency_id(self):
        return self.env.user.company_id.currency_id

    name = fields.Char(string='Name', required=True)

    initials = fields.Char(string='Initials', size=3, required=True)

    minimum_plot_value = fields.Monetary(string='Minimum Plot Value',
                                         currency_field='company_currency_id',
                                         digits=dp.get_precision(
                                             'Product Price'))

    allow_cnab_sending = fields.Boolean(string='Allow CNAB Sending')

    company_currency_id = fields.Many2one('res.currency', string='Currency',
                                          required=True,
                                          default=_default_company_currency_id)
