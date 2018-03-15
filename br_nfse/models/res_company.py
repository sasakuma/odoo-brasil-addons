# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente_nfse = fields.Selection([('1', 'Produção'),
                                           ('2', 'Homologação')],
                                          string='Ambiente NFSe',
                                          default='2')

    senha_ambiente_nfse = fields.Char(string='Senha NFSe',
                                      size=30,
                                      help='Senha Nota Fiscal de Serviço')

    webservice_nfse = fields.Selection(selection=[('nfse_paulistana', 'Nota Fiscal Paulistana')],
                                       string='Webservice NFSe')

    report_nfse_id = fields.Many2one(comodel_name='ir.actions.report',
                                     string='Relatório NFSe')
