from odoo import api, models
from odoo.tools.translate import _


class ResCompany(models.Model):
    _inherit = 'res.company'

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
