# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class BrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'br_account.cfop'
    _description = 'CFOP'

    code = fields.Char(u'Código', size=4, required=True)
    name = fields.Char('Nome', size=256, required=True)
    small_name = fields.Char('Nome Reduzido', size=32, required=True)
    description = fields.Text(u'Descrição')
    type = fields.Selection([('input', u'Entrada'),
                             ('output', u'Saída')],
                            string='Tipo',
                            required=True)
    parent_id = fields.Many2one('br_account.cfop', string='CFOP Pai')
    child_ids = fields.One2many('br_account.cfop', 'parent_id',
                                string='CFOP Filhos')
    internal_type = fields.Selection([('view', u'Visualização'),
                                      ('normal', 'Normal')],
                                     string='Tipo Interno',
                                     required=True,
                                     default='normal')

    _sql_constraints = [
        ('br_account_cfop_code_uniq', 'unique (code)',
         u'Já existe um CFOP com esse código!')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result
