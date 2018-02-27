# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class BrAccountServiceType(models.Model):
    _name = 'br_account.service.type'
    _description = 'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char('Código', size=16, required=True)
    name = fields.Char('Descrição', size=256, required=True)
    parent_id = fields.Many2one(
        'br_account.service.type', 'Tipo de Serviço Pai')
    child_ids = fields.One2many(
        'br_account.service.type', 'parent_id',
        'Tipo de Serviço Filhos')
    internal_type = fields.Selection(
        [('view', 'Visualização'), ('normal', 'Normal')], 'Tipo Interno',
        required=True, default='normal')
    federal_nacional = fields.Float('Imposto Fed. Sobre Serviço Nacional')
    federal_importado = fields.Float('Imposto Fed. Sobre Serviço Importado')
    estadual_imposto = fields.Float('Imposto Estadual')
    municipal_imposto = fields.Float('Imposto Municipal')

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
