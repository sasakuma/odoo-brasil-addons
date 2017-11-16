# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.addons import decimal_precision as dp
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD

STATE = {'edit': [('readonly', False)]}


class InvoiceElectronicItem(models.Model):
    _name = 'invoice.electronic.item'

    name = fields.Text(u'Nome', readonly=True, states=STATE)
    company_id = fields.Many2one(
        'res.company', u'Empresa', index=True, readonly=True, states=STATE)
    invoice_electronic_id = fields.Many2one(
        'invoice.electronic', string=u'Documento', readonly=True, states=STATE)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")
    state = fields.Selection(
        related='invoice_electronic_id.state', string="State")

    product_id = fields.Many2one(
        'product.product', string=u'Produto', readonly=True, states=STATE)
    tipo_produto = fields.Selection(
        [('product', 'Produto'),
         ('service', u'Serviço')],
        string="Tipo Produto", readonly=True, states=STATE)
    cfop = fields.Char(u'CFOP', size=5, readonly=True, states=STATE)
    ncm = fields.Char(u'NCM', size=10, readonly=True, states=STATE)

    uom_id = fields.Many2one(
        'product.uom', string=u'Unidade Medida', readonly=True, states=STATE)
    quantidade = fields.Float(
        string=u'Quantidade', readonly=True, states=STATE)
    preco_unitario = fields.Monetary(
        string=u'Preço Unitário', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    frete = fields.Monetary(
        string=u'Frete', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    seguro = fields.Monetary(
        string=u'Seguro', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    desconto = fields.Monetary(
        string=u'Desconto', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    outras_despesas = fields.Monetary(
        string=u'Outras despesas', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    tributos_estimados = fields.Monetary(
        string=u'Valor Estimado Tributos', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    valor_bruto = fields.Monetary(
        string=u'Valor Bruto', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    valor_liquido = fields.Monetary(
        string=u'Valor Líquido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    indicador_total = fields.Selection([('0', u'0 - Não'),
                                        ('1', u'1 - Sim')],
                                       string=u"Compõe Total da Nota?",
                                       default='1',
                                       readonly=True,
                                       states=STATE)

    origem = fields.Selection(
        ORIGEM_PROD, string=u'Origem Mercadoria', readonly=True, states=STATE)
    icms_cst = fields.Selection(
        CST_ICMS + CSOSN_SIMPLES, string=u'Situação Tributária',
        readonly=True, states=STATE)
    icms_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_tipo_base = fields.Selection(
        [('0', u'0 - Margem Valor Agregado (%)'),
         ('1', u'1 - Pauta (Valor)'),
         ('2', u'2 - Preço Tabelado Máx. (valor)'),
         ('3', u'3 - Valor da operação')],
        string=u'Modalidade BC do ICMS', readonly=True, states=STATE)
    icms_base_calculo = fields.Monetary(
        string=u'Base de cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_aliquota_reducao_base = fields.Float(
        string=u'% Redução Base', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_valor_credito = fields.Monetary(
        string=u"Valor de Cŕedito", digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_aliquota_credito = fields.Float(
        string=u'% de Crédito', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    icms_st_tipo_base = fields.Selection(
        [('0', u'0- Preço tabelado ou máximo  sugerido'),
         ('1', '1 - Lista Negativa (valor)'),
         ('2', '2 - Lista Positiva (valor)'),
         ('3', '3 - Lista Neutra (valor)'),
         ('4', u'4 - Margem Valor Agregado (%)'),
         ('5', '5 - Pauta (valor)')],
        string='Tipo Base ICMS ST', required=True, default='4',
        readonly=True, states=STATE)
    icms_st_aliquota_mva = fields.Float(
        string=u'% MVA', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_base_calculo = fields.Monetary(
        string=u'Base de cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_aliquota_reducao_base = fields.Float(
        string=u'% Redução Base', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    icms_aliquota_diferimento = fields.Float(
        string=u'% Diferimento', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_valor_diferido = fields.Monetary(
        string=u'Valor Diferido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    icms_motivo_desoneracao = fields.Char(
        string=u'Motivo Desoneração', size=2, readonly=True, states=STATE)
    icms_valor_desonerado = fields.Monetary(
        string=u'Valor Desonerado', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ----------- IPI -------------------
    ipi_cst = fields.Selection(CST_IPI, string=u'Situação tributária')
    ipi_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ipi_base_calculo = fields.Monetary(
        string=u'Base de cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ipi_reducao_bc = fields.Float(
        string=u'% Redução Base', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ipi_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ----------- II ----------------------
    ii_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_aliquota = fields.Float(
        string=u'Alíquota II', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_valor_despesas = fields.Monetary(
        string=u'Despesas Aduaneiras', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_valor = fields.Monetary(
        string=u'Imposto de Importação', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_valor_iof = fields.Monetary(
        string=u'IOF', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ------------ PIS ---------------------
    pis_cst = fields.Selection(
        CST_PIS_COFINS, string=u'Situação Tributária',
        readonly=True, states=STATE)
    pis_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    pis_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    pis_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    pis_valor_retencao = fields.Monetary(
        string=u'Valor Retido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ------------ COFINS ------------
    cofins_cst = fields.Selection(
        CST_PIS_COFINS, string=u'Situação Tributária',
        readonly=True, states=STATE)
    cofins_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    cofins_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    cofins_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    cofins_valor_retencao = fields.Monetary(
        string=u'Valor Retido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ----------- ISSQN -------------
    issqn_codigo = fields.Char(
        string=u'Código', size=10, readonly=True, states=STATE)
    issqn_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    issqn_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    issqn_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    issqn_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ------------ RETENÇÔES ------------
    csll_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    csll_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    csll_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    irrf_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    irrf_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    inss_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
