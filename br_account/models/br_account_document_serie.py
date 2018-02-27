# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class BrAccountDocumentSerie(models.Model):
    _name = 'br_account.document.serie'
    _description = 'Série de documentos fiscais'

    code = fields.Char('Código', size=3, required=True)
    name = fields.Char('Descrição', required=True)
    active = fields.Boolean('Ativo')
    fiscal_type = fields.Selection([('service', 'Serviço'),
                                    ('product', 'Produto')],
                                   string='Tipo Fiscal',
                                   default='service')
    fiscal_document_id = fields.Many2one('br_account.fiscal.document',
                                         string='Documento Fiscal',
                                         required=True)
    company_id = fields.Many2one('res.company',
                                 string='Empresa',
                                 required=True)
    internal_sequence_id = fields.Many2one('ir.sequence',
                                           'Sequência Interna')

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every
         new document serie """
        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq).id

    @api.model
    def create(self, vals):
        """ Overwrite method to create a new ir.sequence if
         this field is null """
        if not vals.get('internal_sequence_id'):
            vals.update({'internal_sequence_id': self._create_sequence(vals)})
        return super(BrAccountDocumentSerie, self).create(vals)
