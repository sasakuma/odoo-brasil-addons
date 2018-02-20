from odoo import models, fields


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char('Código IBGE', size=2)
