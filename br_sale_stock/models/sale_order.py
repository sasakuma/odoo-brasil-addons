# © 2014  Renato Lima - Akretion
# © 2013  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            order.update({
                'amount_total': (order.total_bruto - order.total_desconto +
                                 order.total_tax + order.total_frete +
                                 order.total_seguro + order.total_despesas),
            })

    def _calc_ratio(self, qty, total):
        if total > 0:
            return qty / total
        else:
            return 0

    @api.onchange('total_despesas', 'total_seguro', 'total_frete')
    def _onchange_despesas_frete_seguro(self):
        amount = 0
        for line in self.order_line:
            if line.product_id.fiscal_type == 'product':
                amount += line.valor_bruto - line.valor_desconto

        for l in self.order_line:
            if l.product_id.fiscal_type == 'service':
                continue
            item_liquido = l.valor_bruto - l.valor_desconto
            percentual = self._calc_ratio(item_liquido, amount)
            l.update({
                'valor_seguro': self.total_seguro * percentual,
                'valor_frete': self.total_frete * percentual,
                'outras_despesas': self.total_despesas * percentual
            })

    total_despesas = fields.Float(
        string='Despesas ( + )', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    total_seguro = fields.Float(
        string='Seguro ( + )', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    total_frete = fields.Float(
        string='Frete ( + )', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
