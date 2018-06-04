# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


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
        ('employee_expense', 'Employee Expense'),
        ('releases', 'Releases'),
    ]

    date_maturity_current = fields.Date(string='Data de Vencimento')
    date_maturity_origin = fields.Date(string='Data de Vencimento Original')

    origin_type = fields.Selection(string='Origin Type',
                                   selection=ORIGIN_TYPE)

    ref_move_id = fields.Many2one(string='Reference Account Move',
                                  comodel_name='account.move')

    financial_operation_id = fields.Many2one('account.financial.operation',
                                             string='Financial Operation')

    title_type_id = fields.Many2one('account.title.type',
                                    string='Title Type')

    amount_origin = fields.Monetary('Original Amount')

    parcel_id = fields.Many2one(string='Parcel',
                                comodel_name='br_account.invoice.parcel',
                                readonly=True)

    invoice_id = fields.Many2one(comodel_name='account.invoice',
                                 string='Invoice')

    company_currency_id = fields.Many2one('res.currency',
                                          related='company_id.currency_id',
                                          string="Company Currency",
                                          readonly=True,
                                          help='Utility field to express amount currency',
                                          store=True)

    amount_residual = fields.Monetary(string='Residual Amount',
                                      currency_field='company_currency_id',
                                      help="The residual amount on a journal item expressed in the company currency.")

    amount_residual_currency = fields.Monetary(string='Residual Amount in Currency',
                                               help="The residual amount on a journal item expressed in its currency (possibly not the company currency).")

    paid_status = fields.Selection(string='Paid Status',
                                   required=True,
                                   default='open',
                                   selection=[
                                       ('open', 'Open'),
                                       ('partial', 'Partial'),
                                       ('paid', 'Paid'),
                                   ])

    @api.model
    def create(self, values):
        record = super(AccountMove, self).create(values)
        if 'journal_type' in record.env.context:
            journal_type = record.env.context['journal_type']
            if journal_type in ('bank', 'cash'):
                record.origin_type = 'discharge'
            elif journal_type == 'general':
                record.origin_type = 'company_expense'
            else:
                record.origin_type = journal_type
        if 'move_reference' in record.env.context:
            record.ref_move_id = record.env.context['move_reference']
        return record
