# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PaymentOrderLine(models.Model):
    _name = 'payment.order.line'

    @api.multi
    def _compute_state(self):
        for item in self:
            item.state = 'open'
            if item.move_line_id.reconciled:
                item.state = 'paid'

    name = fields.Char(string="Ref.", size=20)
    payment_order_id = fields.Many2one(
        'payment.order', string="Ordem de Pagamento", ondelete="cascade")
    move_line_id = fields.Many2one(
        'account.move.line', string='Linhas de Cobrança')
    partner_id = fields.Many2one(
        'res.partner', related='move_line_id.partner_id',
        string="Parceiro", readonly=True)
    move_id = fields.Many2one('account.move', string="Lançamento de Diário",
                              related='move_line_id.move_id', readonly=True)
    nosso_numero = fields.Char(string="Nosso Número", size=20)
    payment_mode_id = fields.Many2one(
        'payment.mode', string="Modo de pagamento")
    date_maturity = fields.Date(string="Vencimento")
    value = fields.Float(string="Valor", digits=(18, 2))
    state = fields.Selection([("open", "Aberto"),
                              ("paid", "Pago")],
                             string="Situação",
                             compute="_compute_state")


class PaymentOrder(models.Model):
    _name = 'payment.order'

    @api.depends('line_ids')
    def _compute_amount_total(self):
        for item in self:
            amount_total = 0
            for line in item.line_ids:
                amount_total += line.value
            item.amount_total = amount_total

    name = fields.Char(max_length=30, string="Nome", required=True)
    user_id = fields.Many2one('res.users', string='Responsável',
                              required=True)
    payment_mode_id = fields.Many2one('payment.mode',
                                      string='Modo de Pagamento',
                                      required=True)
    state = fields.Selection([('draft', 'Rascunho'), ('cancel', 'Cancelado'),
                              ('open', 'Confirmado'), ('done', 'Fechado')],
                             string="Situação")
    line_ids = fields.One2many('payment.order.line', 'payment_order_id',
                               required=True, string='Linhas de Cobrança')
    currency_id = fields.Many2one('res.currency', string='Moeda')
    amount_total = fields.Float(string="Total",
                                compute='_compute_amount_total')
