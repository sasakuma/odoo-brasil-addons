# © 2009  Gabriel C. Stabel
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from .cst import ORIGEM_PROD


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_type = fields.Selection([('service', 'Serviço'),
                                    ('product', 'Produto')],
                                   string='Tipo Fiscal',
                                   required=True,
                                   default='product')

    origin = fields.Selection(ORIGEM_PROD, 'Origem', default='0')

    fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', string='Classificação Fiscal (NCM)')

    cest = fields.Char(string="CEST", size=10,
                       help="Código Especificador da Substituição Tributária")
    fiscal_observation_ids = fields.Many2many(
        'br_account.fiscal.observation', string="Mensagens Doc. Eletrônico")
