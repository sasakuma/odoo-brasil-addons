# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char('Código BC', size=5)
    ibge_code = fields.Char('Código IBGE', size=5)
    siscomex_code = fields.Char('Código Siscomex', size=4)

