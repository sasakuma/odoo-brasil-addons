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
            rec.has_sale_invoice = any(
                inv.fiscal_document_id.code in ['55'] and inv.state == 'open'
                for inv in self.account_invoice_ids)

    has_sale_invoice = fields.Boolean(string='Sale Invoice',
                                      compute=compute_invoice_type)

    @api.multi
    def action_print_danfe(self):
        """Imprime faturas de venda em lote
        """
        return self.account_invoice_ids.action_print_danfe()
