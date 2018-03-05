# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# © 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    ind_final = fields.Selection([
        ('0', 'Não'),
        ('1', 'Consumidor final')
    ], 'Operação com Consumidor final',
        help='Indica operação com Consumidor final.')
    ind_pres = fields.Selection([
        ('0', 'Não se aplica'),
        ('1', 'Operação presencial'),
        ('2', 'Operação não presencial, pela Internet'),
        ('3', 'Operação não presencial, Teleatendimento'),
        ('4', 'NFC-e em operação com entrega em domicílio'),
        ('9', 'Operação não presencial, outros'),
    ], 'Tipo de operação',
        help='Indicador de presença do comprador no\n'
             'estabelecimento comercial no momento\n'
             'da operação.', default='0')
