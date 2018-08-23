# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


STATE = {'edit': [('readonly', False)]}


class InvoiceElectronicEvent(models.Model):
    _name = 'invoice.electronic.event'
    _order = 'id desc'

    code = fields.Char(string='Código', readonly=True, states=STATE)
    name = fields.Char(string='Mensagem', readonly=True, states=STATE)
    invoice_electronic_id = fields.Many2one(
        'invoice.electronic', string="Fatura Eletrônica",
        readonly=True, states=STATE)
    state = fields.Selection(
        related='invoice_electronic_id.state', string="State")
    category = fields.Selection(string='Tipo', selection=[('info', 'Info'),
                                                          ('warning', 'Aviso'),
                                                          ('error', 'Erro')])
