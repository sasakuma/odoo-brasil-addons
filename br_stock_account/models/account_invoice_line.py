# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _prepare_tax_context(self):
        res = super(AccountInvoiceLine, self)._prepare_tax_context()
        res.update({
            'valor_frete': self.valor_frete,
            'valor_seguro': self.valor_seguro,
            'outras_despesas': self.outras_despesas,
        })
        return res

    @api.one
    @api.depends('valor_frete', 'valor_seguro', 'outras_despesas')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()

        total = (self.valor_bruto - self.valor_desconto +
                 self.valor_frete + self.valor_seguro + self.outras_despesas)
        self.update({'price_total': total})

    valor_frete = fields.Float(
        '(+) Frete', digits=dp.get_precision('Account'), default=0.00)
    valor_seguro = fields.Float(
        '(+) Seguro', digits=dp.get_precision('Account'), default=0.00)
    outras_despesas = fields.Float(
        '(+) Despesas', digits=dp.get_precision('Account'), default=0.00)
