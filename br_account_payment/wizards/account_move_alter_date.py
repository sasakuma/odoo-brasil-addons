from odoo import api, fields, models


class AccountMoveAlterDate(models.TransientModel):
    _name = 'account.move.alter.date'

    old_date_maturity = fields.Date(
        string='Old Date Maturity',
        readonly=True)
    
    new_date_maturity = fields.Date(
        string='New Date Maturity')

    @api.multi
    def alter_date_maturity(self):
        move_id = self.env.context.get('active_id', False)
        if (move_id and self.new_date_maturity
            and self.new_date_maturity != self.old_date_maturity):
            move = self.env['account.move'].browse(move_id)
            move.date_maturity_current = self.new_date_maturity
        return {'type': 'ir.actions.act_window_close'}

    def cancel(self):
        return False
