# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

NFSE_WEBSERVICES = [
    ('nfse_paulistana', 'Nota Fiscal Paulistana'),
    ('nfse_simpliss', 'SIMPLISS'),
    ('nfse_susesu', 'SUSESU'),
    ('nfse_ginfes', 'GINFES'),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente_nfse = fields.Selection([('1', u'Produção'),
                                           ('2', u'Homologação')],
                                          string='Ambiente NFSe',
                                          default='2')

    webservice_nfse = fields.Selection(NFSE_WEBSERVICES,
                                       string='Webservice NFSe')

    senha_ambiente_nfse = fields.Char(string=u'Senha NFSe',
                                      size=30,
                                      help=u'Senha Nota Fiscal de Serviço')
