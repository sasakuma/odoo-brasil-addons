# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class BrAccountFiscalObservation(models.Model):
    _name = 'br_account.fiscal.observation'
    _description = u'Mensagem Documento Eletrônico'
    _order = 'sequence'

    sequence = fields.Integer(u'Sequência', default=1, required=True)
    name = fields.Char(u'Descrição', required=True, size=50)
    message = fields.Text(u'Mensagem', required=True)
    tipo = fields.Selection([('fiscal', u'Observação Fiscal'),
                             ('observacao', u'Observação')], string=u"Tipo")
    document_id = fields.Many2one(
        'br_account.fiscal.document', string="Documento Fiscal")
