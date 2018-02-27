# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection([('0', 'Pagamento à Vista'),
                               ('1', 'Pagamento à Prazo'),
                               ('2', 'Outros')],
                              string='Indicador de Pagamento',
                              default='1')
