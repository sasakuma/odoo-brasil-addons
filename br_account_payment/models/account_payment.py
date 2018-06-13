# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    move_id = fields.Many2one(
        string="Linha de fatura",
        comodel_name='account.move')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if self.env.context.get('default_move_id', False):
            rec['amount'] = self.env.context.get(
                'default_amount', rec.get('amount', 0.0))
        return rec

    def _create_payment_entry(self, amount):
        if self.move_id:
            for line in self.move_id.line_ids:
                if line.account_id == self.move_id.account_id:
                    self = self.with_context(move_line_to_reconcile=line)
            return super(AccountPayment, self)._create_payment_entry(amount)
        else:
            res = super(AccountPayment, self)._create_payment_entry(amount)
            self.move_id = res.id
            return res