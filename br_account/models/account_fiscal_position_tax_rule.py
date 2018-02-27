# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.addons.br_account.models.cst import (CSOSN_SIMPLES, CST_ICMS,
                                               CST_IPI, CST_PIS_COFINS)


class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequência')
    name = fields.Char(string='Descrição', size=100)
    domain = fields.Selection([('icms', 'ICMS'),
                               ('simples', 'Simples Nacional'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
                               ('outros', 'Outros')],
                              string="'Tipo")
    fiscal_position_id = fields.Many2one('account.fiscal.position',
                                         string='Posição Fiscal')

    state_ids = fields.Many2many('res.country.state',
                                 string='Estado Destino',
                                 domain=[('country_id.code', '=', 'BR')])

    product_category_ids = fields.Many2many('product.category',
                                            string='Categoria de Produtos')

    tipo_produto = fields.Selection([('product', 'Produto'),
                                     ('service', 'Serviço')],
                                    string='Tipo produto',
                                    default='product')

    product_ids = fields.Many2many('product.product', string='Produtos')
    partner_ids = fields.Many2many('res.partner', string='Parceiros')

    cst_icms = fields.Selection(CST_ICMS, string='CST ICMS')

    csosn_icms = fields.Selection(CSOSN_SIMPLES, string='CSOSN ICMS')

    cst_pis = fields.Selection(CST_PIS_COFINS, string='CST PIS')

    cst_cofins = fields.Selection(CST_PIS_COFINS, string='CST COFINS')

    cst_ipi = fields.Selection(CST_IPI, string='CST IPI')

    cfop_id = fields.Many2one('br_account.cfop', string='CFOP')

    tax_id = fields.Many2one('account.tax', string='Imposto')

    tax_icms_st_id = fields.Many2one('account.tax',
                                     string='ICMS ST',
                                     domain=[('domain', '=', 'icmsst')])

    icms_aliquota_credito = fields.Float(string='% Crédito de ICMS')
    incluir_ipi_base = fields.Boolean(string='Incl. IPI na base ICMS')
    reducao_icms = fields.Float(string='Redução de base')
    reducao_icms_st = fields.Float(string='Redução de base ST')
    reducao_ipi = fields.Float(string='Redução de base IPI')
    aliquota_mva = fields.Float(string='Alíquota MVA')

    icms_st_aliquota_deducao = fields.Float(string='% ICMS Próprio',
                                            help="Alíquota interna ou interestadual aplicada "  # noqa: 501
                                                 "sobre o valor da operação para deduzir do "  # noqa: 501
                                                 "ICMS ST - Para empresas do Simples Nacional "  # noqa: 501
                                                 "ou usado em casos onde existe apenas ST sem ICMS")  # noqa: 501

    tem_difal = fields.Boolean(string='Aplicar Difal?')

    tax_icms_inter_id = fields.Many2one('account.tax',
                                        help="Alíquota utilizada na operação Interestadual",  # noqa: 501
                                        string='ICMS Inter',
                                        domain=[('domain', '=', 'icms_inter')])
    tax_icms_intra_id = fields.Many2one('account.tax',
                                        help='Alíquota interna do produto no estado destino',  # noqa: 50
                                        string='ICMS Intra',
                                        domain=[('domain', '=', 'icms_intra')])
    tax_icms_fcp_id = fields.Many2one('account.tax',
                                      string='% FCP',
                                      domain=[('domain', '=', 'fcp')])

    issqn_tipo = fields.Selection([('N', 'Normal'),
                                   ('R', 'Retida'),
                                   ('S', 'Substituta'),
                                   ('I', 'Isenta')],
                                  string='Tipo do ISSQN')
