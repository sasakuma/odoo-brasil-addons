# -*- coding: utf-8 -*-
# © 2017 Michell Stuttgart Faria <michellstut@gmail.com>, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    nfse_source_operation_id = fields.Many2one(
        comodel_name='br_account.nfse.source.operation',
        string=u'Natureza da Operação')

    fiscal_document_id_code = fields.Char(string='Fiscal Document Code',
                                          related='fiscal_document_id.code')
