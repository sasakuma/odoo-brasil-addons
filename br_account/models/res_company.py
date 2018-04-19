# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _

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
                                  help="Faturamento Bruto dos últimos 12 "
                                       "meses")

    fiscal_type = fields.Selection(COMPANY_FISCAL_TYPE,
                                   string='Regime Tributário',
                                   required=True,
                                   default=COMPANY_FISCAL_TYPE_DEFAULT)

    cnae_main_id = fields.Many2one('br_account.cnae', string='CNAE Primário')

    cnae_secondary_ids = fields.Many2many('br_account.cnae',
                                          'res_company_br_account_cnae',
                                          'company_id',
                                          'cnae_id',
                                          string='CNAE Secundários')

    accountant_id = fields.Many2one('res.partner', string="Contador")

    @api.multi
    def validate(self):
        error = ''
        if not self.partner_id.legal_name:
            error += _('-Legal Name\n')
        if not self.cnpj_cpf:
            error += _('-CNPJ/CPF \n')
        if not self.district:
            error += _('-District\n')
        if not self.zip:
            error += _('-ZIP\n')
        if not self.city_id:
            error += _('-City\n')
        if not self.country_id:
            error += _('-Country\n')
        if not self.street:
            error += _('-Street\n')
        if not self.number:
            error += _('-Number\n')
        if not self.state_id:
            error += _('-State\n')

        message = _('Company: %s\nMissing Fields:\n%s\n\n')
        if error:
            return message % (self.name, error)
        else:
            return ''
