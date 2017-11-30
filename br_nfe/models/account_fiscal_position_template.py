# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# © 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Consumidor final')
    ], u'Operação com Consumidor final',
        help=u'Indica operação com Consumidor final.')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('9', u'Operação não presencial, outros'),
    ], u'Tipo de operação',
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.', default='0')
