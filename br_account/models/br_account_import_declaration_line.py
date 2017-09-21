# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.addons import decimal_precision as dp


class BrAccountImportDeclarationLine(models.Model):
    _name = 'br_account.import.declaration.line'

    import_declaration_id = fields.Many2one(
        'br_account.import.declaration', u'DI', ondelete='cascade')
    sequence = fields.Integer(u'Sequência', default=1, required=True)
    name = fields.Char(u'Adição', size=3, required=True)
    manufacturer_code = fields.Char(
        u'Código do Fabricante', size=60, required=True)
    amount_discount = fields.Float(
        string=u'Valor', digits=dp.get_precision('Account'), default=0.00)
    drawback_number = fields.Char(u'Número Drawback', size=11)

