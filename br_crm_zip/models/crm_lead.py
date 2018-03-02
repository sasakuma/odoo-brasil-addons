# © 2011  Fabio Negrini - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class CrmLead(models.Model):
    """Extende a model crm.lead para utilizar a consulta de CEP.
    """
    _name = "crm.lead"
    _inherit = ['crm.lead', 'br.zip.abstract']
