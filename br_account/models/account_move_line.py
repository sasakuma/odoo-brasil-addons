# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models
from odoo.tools import float_compare


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    financial_operation_id = fields.Many2one('account.financial.operation',
                                             string='Financial Operation')

    title_type_id = fields.Many2one('account.title.type',
                                    string='Title Type')

    title_value = fields.Float(string='Minimum Plot Value',
                               digits=dp.get_precision('Product Price'))

    # Correção na ordenação do faturamento, remover esse código caso o PR 14852
    # no Odoo seja aceito ou eles corrijam de outra forma
    def _get_pair_to_reconcile(self):
        # field is either 'amount_residual' or 'amount_residual_currency'
        # (if the reconciled account has a secondary currency set)
        field = (self[0].account_id.currency_id and
                 'amount_residual_currency' or
                 'amount_residual')
        rounding = self[0].company_id.currency_id.rounding

        res = [x.amount_currency and
               x.currency_id == self[0].currency_id for x in self]

        if self[0].currency_id and all(res):
            # or if all lines share the same currency
            field = 'amount_residual_currency'
            rounding = self[0].currency_id.rounding
        if self._context.get(
                'skip_full_reconcile_check') == 'amount_currency_excluded':
            field = 'amount_residual'
        elif self._context.get(
                'skip_full_reconcile_check') == 'amount_currency_only':
            field = 'amount_residual_currency'
        # target the pair of move in self that are the oldest
        if self.env.context.get('move_line_to_reconcile', False) and \
                not self.env.context.get('move_line_to_reconcile').reconciled:
            sorted_moves = [self.env.context['move_line_to_reconcile'],
                            self[-1]]
        else:
            sorted_moves = sorted(self, key=lambda a: a.date_maturity)
        debit = credit = False
        for aml in sorted_moves:
            if credit and debit:
                break
            if float_compare(aml[field], 0,
                             precision_rounding=rounding) == 1 and not debit:
                debit = aml
            elif float_compare(aml[field], 0,
                               precision_rounding=rounding) == -1 and \
                    not credit:
                credit = aml
        return debit, credit
