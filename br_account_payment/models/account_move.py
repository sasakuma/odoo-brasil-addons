# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_mode_id = fields.Many2one(
        string="Modo de pagamento",
        comodel_name='payment.mode')

    @api.multi
    def action_register_payment(self):
        dummy, act_id = self.env['ir.model.data'].get_object_reference(
            'account', 'action_account_invoice_payment')
        receivable = (self.account_type == 'receivable')
        vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
        vals['context'] = {
            'default_amount': self.amount,
            'default_partner_type': 'customer' if receivable else 'supplier',
            'default_partner_id': self.partner_id.id,
            'default_communication': self.name,
            'default_payment_type': 'inbound' if receivable else 'outbound',
            'default_move_id': self.id,
        }
        if self.invoice_id:
            vals['context']['default_invoice_ids'] = [(4, self.invoice_id.id, None)]  # noqa: 501
        return vals

    @api.multi
    def action_alter_date_maturity(self):
        ctx = {
            'default_old_date_maturity': self.date_maturity_current,
            'default_new_date_maturity': self.date_maturity_current,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.alter.date',
            'view_type': 'form',
            'view_mode': 'form',
            'context': ctx,
            'views': [(False, "form")],
            'target': 'new',
        }

    @api.multi
    def action_alter_operation(self):
        ctx = {
            'default_old_payment_mode': self.payment_mode_id.id,
            'default_new_payment_mode': self.payment_mode_id.id,
            'default_old_title_type': self.title_type_id.id,
            'default_new_title_type': self.title_type_id.id,
            'default_old_financial_operation': self.financial_operation_id.id,
            'default_new_financial_operation': self.financial_operation_id.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.alter.operation',
            'view_type': 'form',
            'view_mode': 'form',
            'context': ctx,
            'views': [(False, "form")],
            'target': 'new',
        }