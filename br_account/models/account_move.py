# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools import float_is_zero


class AccountMove(models.Model):
    _inherit = 'account.move'

    ORIGIN_TYPE = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('discharge', 'Discharge'),
        ('tax', 'Tax'),
        ('iof', 'IOF'),
        ('reversal_iof', 'Reversal IOF'),
        ('reversal', 'Reversal'),
        ('reversed_discharge', 'Reversed Discharge'),
        ('discount', 'Discount'),
        ('interest', 'Interest'),
        ('reversal_discount', 'Reversal Discount'),
        ('reversal_interest', 'Reversal Interest'),
        ('company_expense', 'Company Expense'),
        ('company_revenue', 'Company Revenue'),
        ('company_renegotiation', 'Company Renegotiation'),
        ('employee_expense', 'Employee Expense'),
        ('releases', 'Releases'),
    ]

    date_maturity_current = fields.Date(
        string='Data de Vencimento')

    date_maturity_origin = fields.Date(
        string='Data de Vencimento Original')

    origin_type = fields.Selection(
        string='Origin Type',
        selection=ORIGIN_TYPE)

    ref_move_id = fields.Many2one(
        string='Reference Account Move',
        comodel_name='account.move')

    financial_operation_id = fields.Many2one(
        string='Financial Operation',
        comodel_name='account.financial.operation')

    title_type_id = fields.Many2one(
        string='Title Type',
        comodel_name='account.title.type')

    amount_origin = fields.Monetary(
        string='Original Amount')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='br_account.invoice.parcel',
        readonly=True)

    invoice_id = fields.Many2one(
        string='Invoice',
        comodel_name='account.invoice',
        readonly=True)

    company_currency_id = fields.Many2one(
        string='Company Currency',
        comodel_name='res.currency',
        related='invoice_id.company_id.currency_id',
        readonly=True,
        store=True,
        help='Utility field to express amount currency')

    amount_residual = fields.Monetary(
        string='Residual Amount',
        currency_field='company_currency_id',
        compute='compute_amount_residual',
        help="The residual amount on a journal item expressed in the"
        " company currency.")

    amount_residual_currency = fields.Monetary(
        string='Residual Amount in Currency',
        compute='compute_amount_residual',
        help="The residual amount on a journal item expressed in its"
        " currency (possibly not the company currency).")

    paid_status = fields.Selection(
        string='Paid Status',
        required=True,
        default='open',
        selection=[
            ('open', 'Open'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),])

    account_id = fields.Many2one(
        string='Account',
        comodel_name='account.account',
        index=True,
        ondelete="cascade",
        domain=[('deprecated', '=', False)],
        default=lambda self: self._context.get('account_id', False))

    account_type = fields.Selection(
        string='Account Type',
        related='account_id.user_type_id.type',
        readonly=True)

    def _journal_type_hook(self):
        return ['sale', 'company_expense', 'company_renegotiation',
        'company_revenue']

    def _account_user_type_hook(self):
        return ['receivable', 'payable']

    @api.model
    def create(self, values):
        rec = super(AccountMove, self).create(values)
        if 'journal_type' in rec.env.context:
            journal_type = rec.env.context['journal_type']
            if journal_type in ('bank', 'cash'):
                rec.origin_type = 'discharge'
            else:
                rec.origin_type = journal_type
        if 'move_reference' in rec.env.context:
            rec.ref_move_id = rec.env.context['move_reference']
        if (rec.journal_id.type in self._journal_type_hook()
            and rec.amount_residual):
            for line in rec.line_ids:
                if line.user_type_id.type in self._account_user_type_hook():
                    line.move_id.account_id = line.account_id
        return rec

    @api.multi
    def write(self, values):
        is_residual_zero = float_is_zero(self.amount_residual, 
            precision_rounding=self.currency_id.rounding)
        if self.account_id:
            if self.currency_id and is_residual_zero:
                values['paid_status'] = 'paid'
            elif abs(self.amount_residual) < self.amount:
                values['paid_status'] = 'partial'
            else:
                values['paid_status'] = 'open'
        return super(AccountMove, self).write(values)

    @api.depends('line_ids.amount_residual_currency', 'line_ids.amount_residual')
    def compute_amount_residual(self):
        """ Computes the residual amount of a move line from a reconciliable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconciliable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
        for record in self:
            for line in record.line_ids:
                if line.user_type_id.type in self._account_user_type_hook():
                    record.amount_residual = abs(line.amount_residual)
                    record.amount_residual_currency = line.amount_residual_currency
