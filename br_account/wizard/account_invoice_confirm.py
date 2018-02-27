import ast

from odoo import api, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountInvoiceConfirm(models.TransientModel):
    _inherit = 'account.invoice.confirm'

    @api.multi
    def br_account_invoice_confirm(self):
        """Criamos um novo metodo de confirmar fatura em lote para que o metodo
         'action_br_account_invoice_open' possa ser chamado. Assim todo o
        faturamento passa pelo mesmo caminho
        """
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        invoices = self.env['account.invoice'].browse(active_ids)

        if any(inv.state not in ('draft', 'proforma', 'proforma2') for inv in invoices):  # noqa: E501
            raise UserError(_("Selected invoice(s) cannot be confirmed as "
                              "they are not in 'Draft' or 'Pro-Forma' "
                              "state."))
        else:
            action = self.env['ir.actions.act_window'].for_xml_id(
                'account', 'action_invoice_tree1')

            context = ast.literal_eval(action['context'])

            for inv in invoices:
                inv.with_context(**context).action_br_account_invoice_open()

        return {'type': 'ir.actions.act_window_close'}
