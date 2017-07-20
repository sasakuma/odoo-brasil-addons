# -*- coding: utf-8 -*-
# @ 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    city_id = fields.Many2one('res.state.city',
                              string='Município')
