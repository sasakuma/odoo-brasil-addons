# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    code_first_digit = fields.Char(compute='_compute_code_first_digit',
                                   string='Primeiro Dígito',
                                   store=True)

    active = fields.Boolean(default=True)

    @api.multi
    @api.depends('code')
    def _compute_code_first_digit(self):
        for rec in self:
            rec.code_first_digit = rec.code[0] if rec.code else ''
