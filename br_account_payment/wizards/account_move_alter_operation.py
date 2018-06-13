from odoo import api, fields, models


class AccountMoveAlterDate(models.TransientModel):
    _name = 'account.move.alter.operation'

    old_title_type = fields.Many2one(
        string='Old Title Type',
        comodel_name='account.title.type',
        readonly=True)
    
    new_title_type = fields.Many2one(
        string='New Title Type',
        comodel_name='account.title.type')

    old_financial_operation = fields.Many2one(
        string='Old Financial Operation',
        comodel_name='account.financial.operation',
        readonly=True)
    
    new_financial_operation = fields.Many2one(
        string='New Financial Operation',
        comodel_name='account.financial.operation')

    old_payment_mode = fields.Many2one(
        string='Old Payment Mode',
        comodel_name='payment.mode',
        readonly=True)

    new_payment_mode = fields.Many2one(
        string='New Payment Mode',
        comodel_name='payment.mode')

    @api.multi
    def alter_operations(self):
        move_id = self.env.context.get('active_id', False)
        move = self.env['account.move'].browse(move_id)
        if (move_id and self.new_title_type
                and self.new_title_type != self.old_title_type):
            move.title_type_id = self.new_title_type.id

        if (move_id and self.new_financial_operation
            and self.new_financial_operation != self.old_financial_operation):
            move.financial_operation_id = self.new_financial_operation.id
            
        if (move_id and self.new_payment_mode
                and self.new_payment_mode != self.old_payment_mode):
            move.payment_mode_id = self.new_payment_mode.id
        return {'type': 'ir.actions.act_window_close'}

    def cancel(self):
        return False
