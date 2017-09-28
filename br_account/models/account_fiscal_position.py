# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', default=_default_company_id)

    position_type = fields.Selection(string=u'Tipo da Posição',
                                     selection=[
                                         ('product', 'Produto'),
                                         ('service', u'Serviço'),
                                     ],
                                     default='product',
                                     required=True)

    company_fiscal_type = fields.Selection(related='company_id.fiscal_type')

    service_type_id = fields.Many2one(comodel_name='br_account.service.type',
                                      string=u'Tipo de Serviço')

    fiscal_document_id = fields.Many2one('br_account.fiscal.document',
                                         string='Documento')

    # TODO Adicionar no domain a empresa (utilizar empresa na posicao fiscal)
    document_serie_id = fields.Many2one('br_account.document.serie',
                                        string=u'Série',
                                        domain="[('fiscal_document_id', '=', fiscal_document_id)]")  # noqa: 501

    journal_id = fields.Many2one('account.journal',
                                 string=u'Diário Contábil',
                                 help=u'Diário Contábil a ser utilizado na fatura.')  # noqa: 501

    account_id = fields.Many2one('account.account',
                                 string=u'Conta Contábil',
                                 help=u'Conta Contábil a ser utilizada na fatura.')  # noqa: 501

    fiscal_observation_ids = fields.Many2many('br_account.fiscal.observation',
                                              string=u'Mensagens Doc. Eletrônico')  # noqa: 501
    note = fields.Text(u'Observações')

    icms_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                        'fiscal_position_id',
                                        string='Regras ICMS',
                                        domain=[('domain', '=', 'icms')])

    simples_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                           'fiscal_position_id',
                                           string='Regras Simples Nacional',
                                           domain=[('domain', '=', 'simples')])

    ipi_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                       'fiscal_position_id',
                                       string='Regras IPI',
                                       domain=[('domain', '=', 'ipi')])

    pis_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                       'fiscal_position_id',
                                       string='Regras PIS',
                                       domain=[('domain', '=', 'pis')])

    cofins_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                          'fiscal_position_id',
                                          string='Regras COFINS',
                                          domain=[('domain', '=', 'cofins')])

    issqn_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                         'fiscal_position_id',
                                         string='Regras ISSQN',
                                         domain=[('domain', '=', 'issqn')])

    ii_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                      'fiscal_position_id',
                                      string='Regras II',
                                      domain=[('domain', '=', 'ii')])

    irrf_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                        'fiscal_position_id',
                                        string='Regras IRRF',
                                        domain=[('domain', '=', 'irrf')])

    csll_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                        'fiscal_position_id',
                                        string='Regras CSLL',
                                        domain=[('domain', '=', 'csll')])

    inss_tax_rule_ids = fields.One2many('account.fiscal.position.tax.rule',
                                        'fiscal_position_id',
                                        string='Regras INSS',
                                        domain=[('domain', '=', 'inss')])

    def _filter_rules(self, fpos_id, type_tax, partner, product, state):
        rule_obj = self.env['account.fiscal.position.tax.rule']

        domain = [
            ('fiscal_position_id', '=', fpos_id),
            ('domain', '=', type_tax),
        ]

        rules = rule_obj.search(domain)
        if rules:
            rules_points = {}
            for rule in rules:
                rules_points[rule.id] = 0
                if rule.tipo_produto == product.fiscal_type:
                    rules_points[rule.id] += 1

                if state in rule.state_ids:
                    rules_points[rule.id] += 1

                if product.categ_id in rule.product_category_ids:
                    rules_points[rule.id] += 1

                if product in rule.product_ids:
                    rules_points[rule.id] += 1

                if len(rule.product_ids) > 0:
                    rules_points[rule.id] -= 1

                if not rule.tipo_produto:
                    rules_points[rule.id] -= 1

                if len(rule.product_category_ids) > 0:
                    rules_points[rule.id] -= 1

                if len(rule.state_ids) > 0:
                    rules_points[rule.id] -= 1

            greater_rule = max([(v, k) for k, v in rules_points.items()])

            if greater_rule[0] <= 0:
                return {}

            rules = [rules.browse(greater_rule[1])]

            return {
                ('%s_rule_id' % type_tax): rules[0],
                'cfop_id': rules[0].cfop_id,
                ('tax_%s_id' % type_tax): rules[0].tax_id,
                # ICMS
                'icms_cst_normal': rules[0].cst_icms,
                'icms_aliquota_reducao_base': rules[0].reducao_icms,
                'incluir_ipi_base': rules[0].incluir_ipi_base,
                # ICMS ST
                'tax_icms_st_id': rules[0].tax_icms_st_id,
                'icms_st_aliquota_mva': rules[0].aliquota_mva,
                'icms_st_aliquota_reducao_base': rules[0].reducao_icms_st,
                'icms_st_aliquota_deducao': rules[0].icms_st_aliquota_deducao,
                # ICMS Difal
                'tem_difal': rules[0].tem_difal,
                'tax_icms_inter_id': rules[0].tax_icms_inter_id,
                'tax_icms_intra_id': rules[0].tax_icms_intra_id,
                'tax_icms_fcp_id': rules[0].tax_icms_fcp_id,
                # Simples
                'icms_csosn_simples': rules[0].csosn_icms,
                'icms_aliquota_credito': rules[0].icms_aliquota_credito,
                # IPI
                'ipi_cst': rules[0].cst_ipi,
                'ipi_reducao_bc': rules[0].reducao_ipi,
                # PIS
                'pis_cst': rules[0].cst_pis,
                # PIS
                'cofins_cst': rules[0].cst_cofins,
                # ISSQN
                'issqn_tipo': rules[0].issqn_tipo,
            }
        else:
            return {}

    @api.model
    def map_tax_extra_values(self, company, product, partner):
        to_state = partner.state_id

        taxes = ('icms', 'simples', 'ipi', 'pis', 'cofins',
                 'issqn', 'ii', 'irrf', 'csll', 'inss')
        res = {}
        for tax in taxes:
            vals = self._filter_rules(
                self.id, tax, partner, product, to_state)
            res.update({k: v for k, v in vals.items() if v})

        return res
