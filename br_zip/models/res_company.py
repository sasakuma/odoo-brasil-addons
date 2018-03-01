# © 2004-2010 Tiny SPRL (<http://tiny.be>)
# © 2016 Danimar Ribeiro, Trustcode
# © 2018 Michell Stuttgart, Multidados
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResCompany(models.Model):
    """Extende a model res.company para utilizar a consulta de CEP.
    """
    _name = 'res.company'
    _inherit = ['res.company', 'br.zip.abstract']
