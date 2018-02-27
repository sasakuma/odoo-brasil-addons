from odoo import api, fields, models


class BrAccountInvoicePrint(models.TransientModel):
    _name = 'br_account.invoice.print'

    def compute_invoice_type(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for rec in self:
            rec.account_invoice_ids = [(6, 0, active_ids)]

    account_invoice_ids = fields.Many2many(comodel_name='account.invoice',
                                           compute=compute_invoice_type,
                                           string='Invoices')
