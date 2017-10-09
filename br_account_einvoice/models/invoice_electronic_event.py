# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


STATE = {'edit': [('readonly', False)]}


class InvoiceElectronicEvent(models.Model):
    _name = 'invoice.electronic.event'
    _order = 'id desc'

    code = fields.Char(string=u'Código', readonly=True, states=STATE)
    name = fields.Char(string=u'Mensagem', readonly=True, states=STATE)
    invoice_electronic_id = fields.Many2one(
        'invoice.electronic', string=u"Fatura Eletrônica",
        readonly=True, states=STATE)
    state = fields.Selection(
        related='invoice_electronic_id.state', string="State")
