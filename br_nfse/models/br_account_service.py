# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class BrAccountServiceType(models.Model):
    _inherit = 'br_account.service.type'

    codigo_tributacao_municipio = fields.Char(string='Cód. Tribut. Munic.',
                                              size=20,
                                              help='Código de Tributação no '
                                                   'Municipio')


class BrAccountNFSeSourceOperation(models.Model):
    _name = 'br_account.nfse.source.operation'

    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Observação', required=True)
