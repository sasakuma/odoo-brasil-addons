# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.br_boleto.boleto.document import getBoletoSelection
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

selection = getBoletoSelection()
IMPLEMENTADOS = ('1', '3', '7', '9', '10')


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    boleto = fields.Boolean(string="Boleto?")
    nosso_numero_sequence = fields.Many2one(
        'ir.sequence', string='Seq. do Nosso Número')
    late_payment_fee = fields.Float(string="Percentual Multa",
                                    digits=dp.get_precision('Account'))
    late_payment_interest = fields.Float(string="Juros de Mora ao Mês",
                                         digits=dp.get_precision('Account'))
    instrucoes = fields.Text(string='Instruções')
    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_variacao = fields.Char('Variação', size=2)
    boleto_cnab_code = fields.Char('Código Convênio', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')
    boleto_type = fields.Selection(
        selection, string="Boleto")
    boleto_especie = fields.Selection([
        ('01', 'DUPLICATA MERCANTIL'),
        ('02', 'NOTA PROMISSÓRIA'),
        ('03', 'NOTA DE SEGURO'),
        ('04', 'MENSALIDADE ESCOLAR'),
        ('05', 'RECIBO'),
        ('06', 'CONTRATO'),
        ('07', 'COSSEGUROS'),
        ('08', 'DUPLICATA DE SERVIÇO'),
        ('09', 'LETRA DE CÂMBIO'),
        ('13', 'NOTA DE DÉBITOS'),
        ('15', 'DOCUMENTO DE DÍVIDA'),
        ('16', 'ENCARGOS CONDOMINIAIS'),
        ('17', 'CONTA DE PRESTAÇÃO DE SERVIÇOS'),
        ('99', 'DIVERSOS'),
    ], string='Espécie do Título', default='01')
    boleto_protesto = fields.Selection([
        ('0', 'Sem instrução'),
        ('1', 'Protestar (Dias Corridos)'),
        ('2', 'Protestar (Dias Úteis)'),
        ('3', 'Não protestar'),
        ('7', 'Negativar (Dias Corridos)'),
        ('8', 'Não Negativar')
    ], string='Códigos de Protesto', default='0')
    boleto_protesto_prazo = fields.Char('Prazo protesto', size=2)

    # @api.onchange("boleto_type")
    # def br_boleto_onchange_boleto_type(self):
    #     vals = {}
    #
    #     if self.boleto_type not in IMPLEMENTADOS:
    #         vals['warning'] = {
    #             'title': u'Ação Bloqueada!',
    #             'message': u'Este boleto ainda não foi implentado!'
    #         }
    #
    #     if self.boleto_type == u'1':
    #         if self.bank_account_id.bank_id.bic != '001':
    #             vals['warning'] = {
    #                 'title': u'Ação Bloqueada!',
    #                 'message': u'Este boleto não combina com a conta
    # bancária!'
    #             }
    #
    #         self.boleto_carteira = u'17'
    #         self.boleto_variacao = u'19'
    #
    #     if self.boleto_type == u'3':
    #         if self.bank_account_id.bank_id.bic != '237':
    #             vals['warning'] = {
    #                 'title': u'Ação Bloqueada!',
    #               'message': u'Este boleto não combina com a conta bancária!'
    #             }
    #         self.boleto_carteira = u'9'
    #
    #     if self.boleto_type == u'7':
    #         if self.bank_account_id.bank_id.bic != '033':
    #             vals['warning'] = {
    #                 'title': u'Ação Bloqueada!',
    #               'message': u'Este boleto não combina com a conta bancária!'
    #             }
    #         self.boleto_carteira = u'101'
    #
    #     if self.boleto_type == u'9':
    #         if self.bank_account_id.bank_id.bic != '756':
    #             vals['warning'] = {
    #                 'title': u'Ação Bloqueada!',
    #               'message': u'Este boleto não combina com a conta bancária!'
    #             }
    #         self.boleto_carteira = u'1'
    #         self.boleto_modalidade = u'01'
    #
    #     if self.boleto_type == u'10':
    #         if self.bank_account_id.bank_id.bic != '0851':
    #             vals['warning'] = {
    #                 'title': u'Ação Bloqueada!',
    #               'message': u'Este boleto não combina com a conta bancária!'
    #             }
    #         self.boleto_carteira = '01'
    #         self.boleto_protesto = '3'
    #
    #     return vals

    @api.onchange("boleto_carteira")
    def br_boleto_onchange_boleto_carteira(self):
        vals = {}

        if self.boleto_type == '9' and len(self.boleto_carteira) != 1:
            vals['warning'] = {
                'title': 'Ação Bloqueada!',
                'message': 'A carteira deste banco possui apenas um digito!'
            }

        return vals
