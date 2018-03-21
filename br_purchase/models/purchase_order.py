# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            price_total = sum(l.price_total for l in order.order_line)
            price_subtotal = sum(l.price_subtotal for l in order.order_line)
            order.update({
                'amount_untaxed': price_subtotal,
                'amount_tax': price_total - price_subtotal,
                'amount_total': price_total,
                'total_tax': price_total - price_subtotal,
                'total_bruto': sum(l.valor_bruto
                                   for l in order.order_line),
            })

    @api.multi
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.fiscal_position_id and self.fiscal_position_id.account_id:
            res['account_id'] = self.fiscal_position_id.account_id.id
        if self.fiscal_position_id and self.fiscal_position_id.journal_id:
            res['journal_id'] = self.fiscal_position_id.journal_id.id
        return res

    total_bruto = fields.Float(
        string='Total Bruto ( = )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True)
    total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True)

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed
        """
        for order in self:
            order.order_line._compute_tax_id()
