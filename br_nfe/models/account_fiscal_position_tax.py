# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# © 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    state_ids = fields.Many2many('res.country.state', string="Estados")
