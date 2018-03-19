# © 2009 Renato Lima - Akretion
# © 2012 Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2018 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()

        if self.fiscal_position_id:
            if self.fiscal_position_id.account_id:
                res['account_id'] = self.fiscal_position_id.account_id.id

            if self.fiscal_position_id.journal_id:
                res['journal_id'] = self.fiscal_position_id.journal_id.id

            if self.fiscal_position_id.fiscal_observation_ids:
                res['fiscal_observation_ids'] = [
                    (6, None, self.fiscal_position_id.fiscal_observation_ids.ids),
                ]
        return res

    total_bruto = fields.Float(string='Total Bruto ( = )',
                               readonly=True,
                               compute='_amount_all',
                               digits=dp.get_precision('Account'), store=True)

    total_tax = fields.Float(string='Impostos ( + )',
                             readonly=True,
                             compute='_amount_all',
                             digits=dp.get_precision('Account'),
                             store=True)

    total_desconto = fields.Float(string='Desconto Total ( - )',
                                  readonly=True,
                                  compute='_amount_all',
                                  digits=dp.get_precision('Account'),
                                  store=True,
                                  help="The discount amount.")

    @api.depends('order_line.price_total', 'order_line.valor_desconto')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            price_total = sum(l.price_total for l in order.order_line)
            price_subtotal = sum(l.price_subtotal for l in order.order_line)
            order.update({
                'total_tax': price_total - price_subtotal,
                'total_desconto': sum(l.valor_desconto for l in order.order_line),
                'total_bruto': sum(l.valor_bruto for l in order.order_line),
            })
