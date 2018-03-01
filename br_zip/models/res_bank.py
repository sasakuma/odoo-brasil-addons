# © 2018 Michell Stuttgart, Multidados
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class ResBank(models.Model):
    """Extende a model res.bank para utilizar a consulta de CEP.
    """
    _name = 'res.bank'
    _inherit = ['res.bank', 'br.zip.abstract']
