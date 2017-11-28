# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.addons import decimal_precision as dp

COMPANY_FISCAL_TYPE = [
    ('1', 'Simples Nacional'),
    ('2', 'Simples Nacional – excesso de sublimite de receita bruta'),
    ('3', 'Regime Normal')
]

COMPANY_FISCAL_TYPE_DEFAULT = '3'


class ResCompany(models.Model):
    _inherit = 'res.company'

    annual_revenue = fields.Float(string='Faturamento Anual',
                                  required=True,
                                  digits=dp.get_precision('Account'),
                                  default=0.00,
                                  help=u"Faturamento Bruto dos últimos 12 "
                                       u"meses")

    fiscal_type = fields.Selection(COMPANY_FISCAL_TYPE,
                                   string=u'Regime Tributário',
                                   required=True,
                                   default=COMPANY_FISCAL_TYPE_DEFAULT)

    cnae_main_id = fields.Many2one('br_account.cnae', string=u'CNAE Primário')

    cnae_secondary_ids = fields.Many2many('br_account.cnae',
                                          'res_company_br_account_cnae',
                                          'company_id',
                                          'cnae_id',
                                          string=u'CNAE Secundários')

    accountant_id = fields.Many2one('res.partner', string="Contador")
