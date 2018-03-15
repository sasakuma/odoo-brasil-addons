# @ 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    city_id = fields.Many2one('res.state.city',
                              string='Município')
