# © 2014  Renato Lima - Akretion
# © 2013  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_tax_context(self):
        res = super(SaleOrderLine, self)._prepare_tax_context()
        res.update({
            'valor_frete': self.valor_frete,
            'valor_seguro': self.valor_seguro,
            'outras_despesas': self.outras_despesas,
        })
        return res

    valor_seguro = fields.Float(
        'Seguro', default=0.0, digits=dp.get_precision('Account'))
    outras_despesas = fields.Float(
        'Despesas', default=0.0, digits=dp.get_precision('Account'))
    valor_frete = fields.Float(
        'Frete', default=0.0, digits=dp.get_precision('Account'))

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['valor_seguro'] = self.valor_seguro
        res['outras_despesas'] = self.outras_despesas
        res['valor_frete'] = self.valor_frete
        return res
