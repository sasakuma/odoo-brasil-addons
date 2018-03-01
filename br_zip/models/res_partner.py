# © 2010-2012  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2018 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    """Extende a model res.partner para utilizar a consulta de CEP.
    """
    _name = 'res.partner'
    _inherit = ['res.partner', 'br.zip.abstract']
