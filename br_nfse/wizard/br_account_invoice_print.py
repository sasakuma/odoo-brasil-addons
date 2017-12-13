# -*- coding: utf-8 -*-

from odoo import api, fields, models


class BrAccountInvoicePrint(models.TransientModel):
    _inherit = 'br_account.invoice.print'

    @api.depends('account_invoice_ids')
    def compute_invoice_type(self):
        super(BrAccountInvoicePrint, self).compute_invoice_type()

        # Verificamos se existe alguma fatura de servico entre as faturas
        # a serem impressas
        for rec in self:
            rec.has_service_invoice = any(
                inv.fiscal_document_id.code in ['001'] and inv.state in ['open', 'paid']
                for inv in self.account_invoice_ids)

    has_service_invoice = fields.Boolean(string='Service Invoice',
                                         compute=compute_invoice_type)

    @api.multi
    def action_print_danfse(self):
        """Imprime faturas de serviço em lote
        """
        return self.account_invoice_ids.action_print_danfse()
