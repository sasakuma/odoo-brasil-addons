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

    origin_type = fields.Selection(string='Origin Type',
                                   selection=ORIGIN_TYPE)

    ref_move_id = fields.Many2one(string='Reference Account Move',
                                  comodel_name='account.move')

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
