# © 2009  Renato Lima - Akretion
# © 2012  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2018 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.addons.br_account.models.cst import (CSOSN_SIMPLES,
                                               CST_ICMS,
                                               CST_IPI,
                                               CST_PIS_COFINS,
                                               ORIGEM_PROD)
from odoo.addons.br_account.models.res_company import COMPANY_FISCAL_TYPE


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _default_company_fiscal_type(self):
        """Retorna valor default para o tipo fiscal
        da empresa.

        Returns:
            str -- Tipo fiscal da empresa (regime normal, simples nacional e etc).
        """

        if self.order_id:
            return self.order_id.company_id.fiscal_type
        else:
            return self.env.user.company_id.fiscal_type

    def _prepare_tax_context(self):
        """Retorna dict para ser utilizado como context do Odoo. Este
        contexto é utilizado durante o calculo das taxas.

        Returns:
            dict -- Dicionario com campos a serem utilizados no context.
        """
        return {
            'incluir_ipi_base': self.incluir_ipi_base,
            'icms_st_aliquota_mva': self.icms_st_aliquota_mva,
            'icms_aliquota_reducao_base': self.icms_aliquota_reducao_base,
            'icms_st_aliquota_reducao_base':
                self.icms_st_aliquota_reducao_base,
            'icms_st_aliquota_deducao': self.icms_st_aliquota_deducao,
            'ipi_reducao_bc': self.ipi_reducao_bc,
            'icms_base_calculo': self.icms_base_calculo,
            'ipi_base_calculo': self.ipi_base_calculo,
            'pis_base_calculo': self.pis_base_calculo,
            'cofins_base_calculo': self.cofins_base_calculo,
            'ii_base_calculo': self.ii_base_calculo,
            'issqn_base_calculo': self.issqn_base_calculo,
        }

    @api.one
    @api.depends('price_unit', 'discount', 'tax_id', 'product_uom_qty',
                 'product_id', 'order_id.partner_id',
                 'order_id.currency_id', 'order_id.company_id',
                 'tax_icms_id', 'tax_icms_st_id', 'tax_icms_inter_id',
                 'tax_icms_intra_id', 'tax_icms_fcp_id', 'tax_ipi_id',
                 'tax_pis_id', 'tax_cofins_id', 'tax_ii_id', 'tax_issqn_id',
                 'tax_csll_id', 'tax_irrf_id', 'tax_inss_id',
                 'incluir_ipi_base', 'tem_difal', 'icms_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_mva', 'tax_simples_id',
                 'icms_st_aliquota_reducao_base', 'icms_aliquota_credito',
                 'icms_st_aliquota_deducao')
    def _compute_price(self):
        """Metodo computavel para calculo do preço total incluindo impostos.
        """
        currency = self.order_id and self.order_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        valor_bruto = self.price_unit * self.product_uom_qty
        desconto = valor_bruto * self.discount / 100.0
        subtotal = valor_bruto - desconto

        taxes = False
        self._update_sale_order_line_ids()
        if self.tax_id:
            ctx = self._prepare_tax_context()

            tax_ids = self.tax_id.with_context(**ctx)

            taxes = tax_ids.compute_all(
                price, currency, self.product_uom_qty, product=self.product_id,
                partner=self.order_id.partner_id)

        icms = ([x for x in taxes['taxes']
                 if x['id'] == self.tax_icms_id.id]) if taxes else []
        icmsst = ([x for x in taxes['taxes']
                   if x['id'] == self.tax_icms_st_id.id]) if taxes else []
        icms_inter = (
            [x for x in taxes['taxes']
             if x['id'] == self.tax_icms_inter_id.id]) if taxes else []
        icms_intra = (
            [x for x in taxes['taxes']
             if x['id'] == self.tax_icms_intra_id.id]) if taxes else []
        icms_fcp = ([x for x in taxes['taxes']
                     if x['id'] == self.tax_icms_fcp_id.id]) if taxes else []
        simples = ([x for x in taxes['taxes']
                    if x['id'] == self.tax_simples_id.id]) if taxes else []
        ipi = ([x for x in taxes['taxes']
                if x['id'] == self.tax_ipi_id.id]) if taxes else []
        pis = ([x for x in taxes['taxes']
                if x['id'] == self.tax_pis_id.id]) if taxes else []
        cofins = ([x for x in taxes['taxes']
                   if x['id'] == self.tax_cofins_id.id]) if taxes else []
        issqn = ([x for x in taxes['taxes']
                  if x['id'] == self.tax_issqn_id.id]) if taxes else []
        ii = ([x for x in taxes['taxes']
               if x['id'] == self.tax_ii_id.id]) if taxes else []
        csll = ([x for x in taxes['taxes']
                 if x['id'] == self.tax_csll_id.id]) if taxes else []
        irrf = ([x for x in taxes['taxes']
                 if x['id'] == self.tax_irrf_id.id]) if taxes else []
        inss = ([x for x in taxes['taxes']
                 if x['id'] == self.tax_inss_id.id]) if taxes else []

        price_subtotal_signed = taxes['total_excluded'] if taxes else subtotal
        if self.order_id.currency_id and self.order_id.currency_id != \
                self.order_id.company_id.currency_id:
            price_subtotal_signed = self.order_id.currency_id.compute(
                price_subtotal_signed, self.order_id.company_id.currency_id)

        self.update({
            'price_total': taxes['total_included'] if taxes else subtotal,
            'price_tax': taxes['total_included'] - taxes['total_excluded']
            if taxes else 0,
            'price_subtotal': taxes['total_excluded'] if taxes else subtotal,
            'valor_bruto': self.product_uom_qty * self.price_unit,
            'valor_desconto': desconto,
            'icms_base_calculo': sum([x['base'] for x in icms]),
            'icms_valor': sum([x['amount'] for x in icms]),
            'icms_st_base_calculo': sum([x['base'] for x in icmsst]),
            'icms_st_valor': sum([x['amount'] for x in icmsst]),
            'icms_bc_uf_dest': sum([x['base'] for x in icms_inter]),
            'icms_uf_remet': sum([x['amount'] for x in icms_inter]),
            'icms_uf_dest': sum([x['amount'] for x in icms_intra]),
            'icms_fcp_uf_dest': sum([x['amount'] for x in icms_fcp]),
            'icms_valor_credito': sum([x['base'] for x in simples]) * (
                self.icms_aliquota_credito / 100),  # noqa: 501
            'ipi_base_calculo': sum([x['base'] for x in ipi]),
            'ipi_valor': sum([x['amount'] for x in ipi]),
            'pis_base_calculo': sum([x['base'] for x in pis]),
            'pis_valor': sum([x['amount'] for x in pis]),
            'cofins_base_calculo': sum([x['base'] for x in cofins]),
            'cofins_valor': sum([x['amount'] for x in cofins]),
            'issqn_base_calculo': sum([x['base'] for x in issqn]),
            'issqn_valor': sum([x['amount'] for x in issqn]),
            'ii_base_calculo': sum([x['base'] for x in ii]),
            'ii_valor': sum([x['amount'] for x in ii]),
            'csll_base_calculo': sum([x['base'] for x in csll]),
            'csll_valor': sum([x['amount'] for x in csll]),
            'inss_base_calculo': sum([x['base'] for x in inss]),
            'inss_valor': sum([x['amount'] for x in inss]),
            'irrf_base_calculo': sum([x['base'] for x in irrf]),
            'irrf_valor': sum([x['amount'] for x in irrf]),
        })

    @api.multi
    @api.depends('icms_cst_normal', 'icms_csosn_simples',
                 'company_fiscal_type')
    def _compute_cst_icms(self):
        """Metodo computavel para atribuição do valor do campo cst_icms.
        """
        for item in self:
            item.icms_cst = item.icms_cst_normal \
                if item.company_fiscal_type == '3' else item.icms_csosn_simples

    price_tax = fields.Float(
        compute='_compute_price', string='Impostos', store=True,
        digits=dp.get_precision('Account'))
    price_total = fields.Float(
        'Valor Líquido', digits=dp.get_precision('Account'), store=True,
        default=0.00, compute='_compute_price')
    valor_desconto = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    valor_bruto = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    tributos_estimados = fields.Float(
        string='Total Est. Tributos', default=0.00,
        digits=dp.get_precision('Account'))
    tributos_estimados_federais = fields.Float(
        string='Tributos Federais', default=0.00,
        digits=dp.get_precision('Account'))
    tributos_estimados_estaduais = fields.Float(
        string='Tributos Estaduais', default=0.00,
        digits=dp.get_precision('Account'))
    tributos_estimados_municipais = fields.Float(
        string='Tributos Municipais', default=0.00,
        digits=dp.get_precision('Account'))

    rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    cfop_id = fields.Many2one('br_account.cfop', 'CFOP')
    fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', 'Classificação Fiscal')
    product_type = fields.Selection(
        [('product', 'Produto'), ('service', 'Serviço')],
        string='Tipo do Produto', required=True, default='product')
    company_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE,
        default=_default_company_fiscal_type, string='Regime Tributário')
    calculate_tax = fields.Boolean(string='Calcular Imposto', default=True)
    fiscal_comment = fields.Text('Observação Fiscal')
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Posição Fiscal',
        related='order_id.fiscal_position_id')
    fiscal_position_type = fields.Selection(
        string='Tipo Fiscal do Produto',
        related='fiscal_position_id.position_type')

    # =========================================================================
    # ICMS Normal
    # =========================================================================
    icms_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_icms_id = fields.Many2one('account.tax', string="Alíquota ICMS",
                                  domain=[('domain', '=', 'icms')])
    icms_cst = fields.Char('CST ICMS', size=10,
                           store=True, compute='_compute_cst_icms')
    icms_cst_normal = fields.Selection(CST_ICMS, string="CST ICMS")
    icms_origem = fields.Selection(ORIGEM_PROD, 'Origem', default='0')
    icms_tipo_base = fields.Selection(
        [('0', '0 - Margem Valor Agregado (%)'),
         ('1', '1 - Pauta (valor)'),
         ('2', '2 - Preço Tabelado Máximo (valor)'),
         ('3', '3 - Valor da Operação')],
        'Tipo Base ICMS', required=True, default='3')
    incluir_ipi_base = fields.Boolean(
        string="Incl. Valor IPI?",
        help="Se marcado o valor do IPI inclui a base de cálculo")
    icms_base_calculo = fields.Float(
        'Base ICMS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_valor = fields.Float(
        'Valor ICMS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_aliquota = fields.Float(
        'Perc ICMS', digits=dp.get_precision('Discount'), default=0.00)
    icms_aliquota_reducao_base = fields.Float(
        '% Red. Base ICMS', digits=dp.get_precision('Discount'),
        default=0.00)

    # =========================================================================
    # ICMS Substituição
    # =========================================================================
    tax_icms_st_id = fields.Many2one('account.tax', string="Alíquota ICMS ST",
                                     domain=[('domain', '=', 'icmsst')])
    icms_st_tipo_base = fields.Selection(
        [('0', '0 - Preço tabelado ou máximo  sugerido'),
         ('1', '1 - Lista Negativa (valor)'),
         ('2', '2 - Lista Positiva (valor)'),
         ('3', '3 - Lista Neutra (valor)'),
         ('4', '4 - Margem Valor Agregado (%)'),
         ('5', '5 - Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_valor = fields.Float(
        'Valor ICMS ST', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_base_calculo = fields.Float(
        'Base ICMS ST', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_aliquota = fields.Float(
        '% ICMS ST', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_aliquota_reducao_base = fields.Float(
        '% Red. Base ST',
        digits=dp.get_precision('Discount'))
    icms_st_aliquota_mva = fields.Float(
        'MVA Ajustado ST',
        digits=dp.get_precision('Discount'), default=0.00)

    # =========================================================================
    # ICMS Difal
    # =========================================================================
    tem_difal = fields.Boolean(
        'Difal?', digits=dp.get_precision('Discount'))
    icms_bc_uf_dest = fields.Float(
        'Base ICMS', compute='_compute_price',
        digits=dp.get_precision('Discount'))
    tax_icms_inter_id = fields.Many2one(
        'account.tax', help="Alíquota utilizada na operação Interestadual",
        string="ICMS Inter", domain=[('domain', '=', 'icms_inter')])
    tax_icms_intra_id = fields.Many2one(
        'account.tax', help="Alíquota interna do produto no estado destino",
        string="ICMS Intra", domain=[('domain', '=', 'icms_intra')])
    tax_icms_fcp_id = fields.Many2one(
        'account.tax', string="% FCP", domain=[('domain', '=', 'fcp')])
    icms_aliquota_inter_part = fields.Float(
        '% Partilha', default=40.0, digits=dp.get_precision('Discount'))
    icms_fcp_uf_dest = fields.Float(
        string='Valor FCP', compute='_compute_price',
        digits=dp.get_precision('Discount'), )
    icms_uf_dest = fields.Float(
        'ICMS Destino', compute='_compute_price',
        digits=dp.get_precision('Discount'))
    icms_uf_remet = fields.Float(
        'ICMS Remetente', compute='_compute_price',
        digits=dp.get_precision('Discount'))

    # =========================================================================
    # ICMS Simples Nacional
    # =========================================================================
    tax_simples_id = fields.Many2one(
        'account.tax', help="Alíquota utilizada no Simples Nacional",
        string="Alíquota Simples", domain=[('domain', '=', 'simples')])
    icms_csosn_simples = fields.Selection(CSOSN_SIMPLES, string="CSOSN ICMS")
    icms_aliquota_credito = fields.Float("% Cŕedito ICMS")
    icms_valor_credito = fields.Float(
        "Valor de Crédito", compute='_compute_price', store=True)
    icms_st_aliquota_deducao = fields.Float(
        string="% ICMS Próprio",
        help="Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional ou usado em casos onde existe apenas ST sem ICMS")

    # =========================================================================
    # ISSQN
    # =========================================================================
    issqn_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra')
    tax_issqn_id = fields.Many2one('account.tax', string="Alíquota ISSQN",
                                   domain=[('domain', '=', 'issqn')])
    issqn_tipo = fields.Selection([('N', 'Normal'),
                                   ('R', 'Retida'),
                                   ('S', 'Substituta'),
                                   ('I', 'Isenta')],
                                  string='Tipo do ISSQN',
                                  required=True, default='N')
    service_type_id = fields.Many2one(
        'br_account.service.type', 'Tipo de Serviço', store=True)
    issqn_base_calculo = fields.Float(
        'Base ISSQN', digits=dp.get_precision('Account'),
        compute='_compute_price', store=True)
    issqn_aliquota = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    issqn_valor = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)

    # =========================================================================
    # IPI
    # =========================================================================
    ipi_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_ipi_id = fields.Many2one('account.tax', string="Alíquota IPI",
                                 domain=[('domain', '=', 'ipi')])
    ipi_tipo = fields.Selection(
        [('percent', 'Percentual')],
        'Tipo do IPI', required=True, default='percent')
    ipi_base_calculo = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True, )
    ipi_reducao_bc = fields.Float(
        '% Redução Base', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_valor = fields.Float(
        'Valor IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    ipi_aliquota = fields.Float(
        'Perc IPI', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    ipi_cst = fields.Selection(CST_IPI, string='CST IPI')

    # =========================================================================
    # PIS
    # =========================================================================
    pis_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_pis_id = fields.Many2one('account.tax', string="Alíquota PIS",
                                 domain=[('domain', '=', 'pis')])
    pis_cst = fields.Selection(CST_PIS_COFINS, 'CST PIS')
    pis_tipo = fields.Selection([('percent', 'Percentual')],
                                string='Tipo do PIS', required=True,
                                default='percent')
    pis_base_calculo = fields.Float(
        'Base PIS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    pis_valor = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    pis_aliquota = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)

    # =========================================================================
    # COFINS
    # =========================================================================
    cofins_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra')
    tax_cofins_id = fields.Many2one('account.tax', string="Alíquota COFINS",
                                    domain=[('domain', '=', 'cofins')])
    cofins_cst = fields.Selection(CST_PIS_COFINS, 'CST COFINS')
    cofins_tipo = fields.Selection([('percent', 'Percentual')],
                                   string='Tipo do COFINS', required=True,
                                   default='percent')
    cofins_base_calculo = fields.Float(
        'Base COFINS', compute='_compute_price', store=True,
        digits=dp.get_precision('Account'))
    cofins_valor = fields.Float(
        'Valor COFINS', digits=dp.get_precision('Account'),
        compute='_compute_price', store=True)
    cofins_aliquota = fields.Float(
        'Perc COFINS', digits=dp.get_precision('Discount'))

    # =========================================================================
    # Imposto de importação
    # =========================================================================
    ii_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_ii_id = fields.Many2one('account.tax', string="Alíquota II",
                                domain=[('domain', '=', 'ii')])
    ii_base_calculo = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    ii_aliquota = fields.Float(
        '% II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_valor = fields.Float(
        'Valor II', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    ii_valor_iof = fields.Float(
        'Valor IOF', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_valor_despesas = fields.Float(
        'Desp. Aduaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    import_declaration_ids = fields.One2many(
        'br_account.import.declaration',
        'invoice_line_id', 'Declaração de Importação')

    # =========================================================================
    # Impostos de serviço - CSLL
    # =========================================================================
    csll_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_csll_id = fields.Many2one('account.tax', string="Alíquota CSLL",
                                  domain=[('domain', '=', 'csll')])
    csll_base_calculo = fields.Float(
        'Base CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    csll_valor = fields.Float(
        'Valor CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    csll_aliquota = fields.Float(
        'Perc CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    # =========================================================================
    # Impostos de serviço - IRRF
    # =========================================================================
    irrf_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_irrf_id = fields.Many2one('account.tax', string="Alíquota IRRF",
                                  domain=[('domain', '=', 'irrf')])
    irrf_base_calculo = fields.Float(
        'Base IRRF', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    irrf_valor = fields.Float(
        'Valor IRFF', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    irrf_aliquota = fields.Float(
        'Perc IRRF', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    # =========================================================================
    # Impostos de serviço - INSS
    # =========================================================================
    inss_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')

    tax_inss_id = fields.Many2one('account.tax', string="Alíquota INSS",
                                  domain=[('domain', '=', 'inss')])
    inss_base_calculo = fields.Float(
        'Base INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    inss_valor = fields.Float(
        'Valor INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    inss_aliquota = fields.Float(
        'Perc INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    informacao_adicional = fields.Text(string="Informações Adicionais")

    percent_subtotal = fields.Float(
        string='Percent Total', compute='_compute_percent_subtotal')

    @api.depends('price_subtotal', 'order_id.total_bruto')
    def _compute_percent_subtotal(self):
        """Calcula porcentagem do preço total da linha sobre o total da fatura.
        """

        for line in self:
            if line.order_id.total_bruto:
                line.percent_subtotal = round(
                    line.price_subtotal / line.order_id.total_bruto, 6)

    def _update_tax_from_ncm(self):
        """Atualiza taxas a partir do ncm (classificação fiscal).
        """
        if self.product_id:
            ncm = self.product_id.fiscal_classification_id
            taxes = ncm.tax_icms_st_id | ncm.tax_ipi_id

            self.update({
                'icms_st_aliquota_mva': ncm.icms_st_aliquota_mva,
                'icms_st_aliquota_reducao_base':
                    ncm.icms_st_aliquota_reducao_base,
                'ipi_cst': ncm.ipi_cst,
                'ipi_reducao_bc': ncm.ipi_reducao_bc,
                'tax_icms_st_id': ncm.tax_icms_st_id.id,
                'tax_ipi_id': ncm.tax_ipi_id.id,
                'tax_id': [(6, None, [x.id for x in taxes if x])]
            })

    def _set_taxes(self):
        """Utilizado no onchange para setar o valor de atribuir 
        impostos e preços. Atualza o campo tax_id, responsável
        pelo impostos do sale.order.line.
        """

        taxes = self.product_id.taxes_id

        # Keep only taxes of the company
        company_id = self.company_id or self.env.user.company_id
        taxes = taxes.filtered(lambda r: r.company_id == company_id)

        self.tax_id = fp_taxes = self.order_id.fiscal_position_id.map_tax(
            taxes, self.product_id, self.order_id.partner_id)

        fix_price = self.env['account.tax']._fix_tax_included_price
        self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)

        self._update_tax_from_ncm()
        fpos = self.order_id.fiscal_position_id

        if fpos:
            vals = fpos.map_tax_extra_values(
                self.company_id, self.product_id, self.order_id.partner_id)

            for key, value in vals.items():
                if value and key in self._fields:
                    self.update({key: value})

        self.tax_id = (self.tax_icms_id |
                       self.tax_icms_st_id |
                       self.tax_icms_inter_id |
                       self.tax_icms_intra_id |
                       self.tax_icms_fcp_id |
                       self.tax_simples_id |
                       self.tax_ipi_id |
                       self.tax_pis_id |
                       self.tax_cofins_id |
                       self.tax_issqn_id |
                       self.tax_ii_id |
                       self.tax_csll_id |
                       self.tax_irrf_id |
                       self.tax_inss_id)

    def _set_extimated_taxes(self, price):
        """Calcula valor para os tributos estimados
        (federal, estaual e nacional).

        Arguments:
            price {float} -- preço do produto.
        """

        service = self.fiscal_position_id.service_type_id
        ncm = self.product_id.fiscal_classification_id

        if self.product_type == 'service':
            self.tributos_estimados_federais = price * (service.federal_nacional / 100)  # noqa: 501
            self.tributos_estimados_estaduais = price * (service.estadual_imposto / 100)  # noqa: 501
            self.tributos_estimados_municipais = price * (service.municipal_imposto / 100)  # noqa: 501
        else:
            if self.icms_origem in ('1', '2', '3', '8'):
                federal = ncm.federal_nacional
            else:
                federal = ncm.federal_importado

            self.tributos_estimados_federais = price * (federal / 100)
            self.tributos_estimados_estaduais = price * (ncm.estadual_imposto / 100)  # noqa: 501
            self.tributos_estimados_municipais = price * (ncm.municipal_imposto / 100)  # noqa: 501

        self.tributos_estimados = (self.tributos_estimados_federais +
                                   self.tributos_estimados_estaduais +
                                   self.tributos_estimados_municipais)

    def _update_sale_order_line_ids(self):
        """Atializa o campo de impostos tax_id da sale.order.line.
        """

        other_taxes = self.tax_id.filtered(
            lambda x: not x.domain)
        self.tax_id = (other_taxes |
                       self.tax_icms_id |
                       self.tax_icms_st_id |
                       self.tax_icms_inter_id |
                       self.tax_icms_intra_id |
                       self.tax_icms_fcp_id |
                       self.tax_simples_id |
                       self.tax_ipi_id |
                       self.tax_pis_id |
                       self.tax_cofins_id |
                       self.tax_issqn_id |
                       self.tax_ii_id |
                       self.tax_csll_id |
                       self.tax_irrf_id |
                       self.tax_inss_id)

    @api.onchange('product_id')
    def _br_sale_onchange_product_id(self):
        """Metodo onchange para o campo 'product_id'.
        Realiza o preenchimento dos impostos a partir da posição fiscal.
        """
        self._set_taxes()
        self.product_type = self.product_id.fiscal_type
        self.icms_origem = self.product_id.origin
        ncm = self.product_id.fiscal_classification_id
        service = self.fiscal_position_id.service_type_id
        self.fiscal_classification_id = ncm.id
        self.service_type_id = service.id

        self._set_extimated_taxes(self.product_id.lst_price)

    @api.onchange('price_subtotal')
    def _onchange_price_subtotal(self):
        """Metodo onchange para o campo 'price_subtotal'.
        """
        self._set_extimated_taxes(self.price_subtotal)

    @api.onchange('tax_icms_id')
    def _onchange_tax_icms_id(self):
        """Metodo onchange para o campo 'tax_icms_id'.
        """
        if self.tax_icms_id:
            self.icms_aliquota = self.tax_icms_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_icms_st_id')
    def _onchange_tax_icms_st_id(self):
        """Metodo onchange para o campo 'tax_icms_st_id'.
        """
        if self.tax_icms_st_id:
            self.icms_st_aliquota = self.tax_icms_st_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_icms_inter_id')
    def _onchange_tax_icms_inter_id(self):
        """Metodo onchange para o campo 'tax_icms_inter_id'.
        """
        self._update_sale_order_line_ids()

    @api.onchange('tax_icms_intra_id')
    def _onchange_tax_icms_intra_id(self):
        """Metodo onchange para o campo 'tax_icms_intra_id'.
        """
        self._update_sale_order_line_ids()

    @api.onchange('tax_icms_fcp_id')
    def _onchange_tax_icms_fcp_id(self):
        """Metodo onchange para o campo 'tax_icms_fcp_id'.
        """
        self._update_sale_order_line_ids()

    @api.onchange('tax_simples_id')
    def _onchange_tax_simples_id(self):
        """Metodo onchange para o campo 'tax_simples_id'.
        """
        self._update_sale_order_line_ids()

    @api.onchange('tax_pis_id')
    def _onchange_tax_pis_id(self):
        """Metodo onchange para o campo 'tax_pis_id'.
        """
        if self.tax_pis_id:
            self.pis_aliquota = self.tax_pis_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_cofins_id')
    def _onchange_tax_cofins_id(self):
        """Metodo onchange para o campo 'tax_cofins_id'.
        """
        if self.tax_cofins_id:
            self.cofins_aliquota = self.tax_cofins_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_ipi_id')
    def _onchange_tax_ipi_id(self):
        """Metodo onchange para o campo 'tax_ipi_id'.
        """
        if self.tax_ipi_id:
            self.ipi_aliquota = self.tax_ipi_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_ii_id')
    def _onchange_tax_ii_id(self):
        """Metodo onchange para o campo 'tax_ii_id'.
        """
        if self.tax_ii_id:
            self.ii_aliquota = self.tax_ii_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_issqn_id')
    def _onchange_tax_issqn_id(self):
        """Metodo onchange para o campo 'tax_issqn_id'.
        """
        if self.tax_issqn_id:
            self.issqn_aliquota = self.tax_issqn_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_csll_id')
    def _onchange_tax_csll_id(self):
        """Metodo onchange para o campo 'tax_csll_id'.
        """
        if self.tax_csll_id:
            self.csll_aliquota = self.tax_csll_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_irrf_id')
    def _onchange_tax_irrf_id(self):
        """Metodo onchange para o campo 'tax_irrf_id'.
        """
        if self.tax_irrf_id:
            self.irrf_aliquota = self.tax_irrf_id.amount
        self._update_sale_order_line_ids()

    @api.onchange('tax_inss_id')
    def _onchange_tax_inss_id(self):
        """Metodo onchange para o campo 'tax_inss_id'.
        """
        if self.tax_inss_id:
            self.inss_aliquota = self.tax_inss_id.amount
        self._update_sale_order_line_ids()

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'icms_st_aliquota_mva', 'incluir_ipi_base',
                 'icms_aliquota_reducao_base', 'icms_st_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_deducao')
    def _compute_amount(self):
        """Calcula total da sale.order.line adicionando os impostos.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            ctx = line._prepare_tax_context()
            tax_ids = line.tax_id.with_context(**ctx)
            taxes = tax_ids.compute_all(
                price, line.order_id.currency_id,
                line.product_uom_qty, product=line.product_id,
                partner=line.order_id.partner_id)

            valor_bruto = line.price_unit * line.product_uom_qty
            desconto = valor_bruto * line.discount / 100.0
            desconto = line.order_id.pricelist_id.currency_id.round(desconto)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'valor_bruto': valor_bruto,
                'valor_desconto': desconto,
            })

    @api.multi
    def _compute_tax_id(self):
        res = super(SaleOrderLine, self)._compute_tax_id()
        for line in self:
            line._update_tax_from_ncm()
            fpos = (line.order_id.fiscal_position_id or
                    line.order_id.partner_id.property_account_position_id)
            if fpos:
                vals = fpos.map_tax_extra_values(
                    line.company_id, line.product_id, line.order_id.partner_id)

                for key, value in list(vals.items()):
                    if value and key in line._fields:
                        line.update({key: value})

                empty = line.env['account.tax'].browse()
                ipi = line.tax_id.filtered(lambda x: x.domain == 'ipi')
                icmsst = line.tax_id.filtered(lambda x: x.domain == 'icmsst')
                tax_ids = (vals.get('tax_icms_id', empty) |
                           vals.get('tax_icms_st_id', icmsst) |
                           vals.get('tax_icms_inter_id', empty) |
                           vals.get('tax_icms_intra_id', empty) |
                           vals.get('tax_icms_fcp_id', empty) |
                           vals.get('tax_simples_id', empty) |
                           vals.get('tax_ipi_id', ipi) |
                           vals.get('tax_pis_id', empty) |
                           vals.get('tax_cofins_id', empty) |
                           vals.get('tax_ii_id', empty) |
                           vals.get('tax_issqn_id', empty))

                line.update({
                    'tax_id': [(6, None, [x.id for x in tax_ids if x])]
                })

        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        """Prepara os valores para serem utilizados durante a criação da
        invoice.line a partir da confirmação da sale.order.

        Arguments:
            qty {int} -- Quantidade do produto presente na sale.order.line.

        Returns:
            dict -- Dicionario contendo os valores para criação da linha da fatura.
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['valor_desconto'] = self.valor_desconto
        res['valor_bruto'] = self.valor_bruto

        # Improve this one later
        icms = self.tax_id.filtered(lambda x: x.domain == 'icms')
        icmsst = self.tax_id.filtered(lambda x: x.domain == 'icmsst')
        icms_inter = self.tax_id.filtered(lambda x: x.domain == 'icms_inter')
        icms_intra = self.tax_id.filtered(lambda x: x.domain == 'icms_intra')
        icms_fcp = self.tax_id.filtered(lambda x: x.domain == 'icms_fcp')
        simples = self.tax_id.filtered(lambda x: x.domain == 'simples')
        ipi = self.tax_id.filtered(lambda x: x.domain == 'ipi')
        pis = self.tax_id.filtered(lambda x: x.domain == 'pis')
        cofins = self.tax_id.filtered(lambda x: x.domain == 'cofins')
        ii = self.tax_id.filtered(lambda x: x.domain == 'ii')
        issqn = self.tax_id.filtered(lambda x: x.domain == 'issqn')
        csll = self.tax_id.filtered(lambda x: x.domain == 'csll')
        irrf = self.tax_id.filtered(lambda x: x.domain == 'irrf')
        inss = self.tax_id.filtered(lambda x: x.domain == 'inss')

        res['icms_cst_normal'] = self.icms_cst_normal
        res['icms_csosn_simples'] = self.icms_csosn_simples

        res['tax_icms_id'] = icms and icms.id or False
        res['tax_icms_st_id'] = icmsst and icmsst.id or False
        res['tax_icms_inter_id'] = icms_inter and icms_inter.id or False
        res['tax_icms_intra_id'] = icms_intra and icms_intra.id or False
        res['tax_icms_fcp_id'] = icms_fcp and icms_fcp.id or False
        res['tax_simples_id'] = simples and simples.id or False
        res['tax_ipi_id'] = ipi and ipi.id or False
        res['tax_pis_id'] = pis and pis.id or False
        res['tax_cofins_id'] = cofins and cofins.id or False
        res['tax_ii_id'] = ii and ii.id or False
        res['tax_issqn_id'] = issqn and issqn.id or False
        res['tax_csll_id'] = csll and csll.id or False
        res['tax_irrf_id'] = irrf and irrf.id or False
        res['tax_inss_id'] = inss and inss.id or False

        res['product_type'] = self.product_id.fiscal_type
        res['company_fiscal_type'] = self.company_id.fiscal_type
        res['cfop_id'] = self.cfop_id.id

        ncm = self.product_id.fiscal_classification_id
        service = self.fiscal_position_id.service_type_id

        res['fiscal_classification_id'] = ncm.id
        res['service_type_id'] = service.id
        res['icms_origem'] = self.product_id.origin

        if self.product_id.fiscal_type == 'service':
            res['tributos_estimados_federais'] = self.price_subtotal * (service.federal_nacional / 100)  # noqa: 501
            res['tributos_estimados_estaduais'] = self.price_subtotal * (service.estadual_imposto / 100)  # noqa: 501
            res['tributos_estimados_municipais'] = self.price_subtotal * (service.municipal_imposto / 100)  # noqa: 501
        else:
            if self.product_id.origin in ('1', '2', '3', '8'):
                federal = ncm.federal_nacional
            else:
                federal = ncm.federal_importado

            res['tributos_estimados_federais'] = self.price_subtotal * (federal / 100)  # noqa: 501
            res['tributos_estimados_estaduais'] = self.price_subtotal * (ncm.estadual_imposto / 100)  # noqa: 501
            res['tributos_estimados_municipais'] = self.price_subtotal * (ncm.municipal_imposto / 100)  # noqa: 501

        res['tributos_estimados'] = (res['tributos_estimados_federais'] +
                                     res['tributos_estimados_estaduais'] +
                                     res['tributos_estimados_municipais'])

        res['incluir_ipi_base'] = self.incluir_ipi_base

        res['icms_aliquota'] = icms.amount or 0.0
        res['icms_st_aliquota_mva'] = self.icms_st_aliquota_mva or 0.0
        res['icms_st_aliquota'] = icmsst.amount or 0.0
        res['icms_aliquota_inter_part'] = self.icms_aliquota_inter_part or 0.0
        res['icms_aliquota_reducao_base'] = self.icms_aliquota_reducao_base or 0.0
        res['icms_st_aliquota_reducao_base'] = self.icms_st_aliquota_reducao_base or 0.0
        res['icms_st_aliquota_deducao'] = self.icms_st_aliquota_deducao or 0.0
        res['icms_aliquota_credito'] = self.icms_aliquota_credito or 0.0
        res['tem_difal'] = self.tem_difal
        res['icms_uf_remet'] = icms_inter.amount or 0.0
        res['icms_uf_dest'] = icms_intra.amount or 0.0
        res['icms_fcp_uf_dest'] = icms_fcp.amount or 0.0
        res['icms_csosn_simples'] = self.icms_csosn_simples
        res['icms_origem'] = self.icms_origem
        res['incluir_ipi_base'] = self.incluir_ipi_base
        res['icms_rule_id'] = self.icms_rule_id.id

        res['ipi_cst'] = self.ipi_cst
        res['ipi_aliquota'] = ipi.amount or 0.0
        res['ipi_reducao_bc'] = self.ipi_reducao_bc
        res['ipi_rule_id'] = self.ipi_rule_id.id

        res['pis_cst'] = self.pis_cst
        res['pis_tipo'] = self.pis_tipo
        res['pis_aliquota'] = pis.amount or 0.0
        res['pis_rule_id'] = self.pis_rule_id.id

        res['cofins_cst'] = self.cofins_cst
        res['cofins_tipo'] = self.cofins_tipo
        res['cofins_aliquota'] = cofins.amount or 0.0
        res['cofins_rule_id'] = self.cofins_rule_id.id

        res['issqn_aliquota'] = issqn.amount or 0.0
        res['issqn_tipo'] = self.issqn_tipo

        res['ii_aliquota'] = ii.amount or 0.0
        res['ii_valor_despesas'] = self.ii_valor_despesas or 0.0
        res['ii_valor_iof'] = self.ii_valor_iof or 0.0
        res['ii_rule_id'] = self.ii_rule_id.id

        res['csll_rule_id'] = self.csll_rule_id.id
        res['irrf_rule_id'] = self.irrf_rule_id.id
        res['inss_rule_id'] = self.inss_rule_id.id

        return res
