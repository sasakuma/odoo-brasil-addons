# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        error = ''
        msg_error = _('Action Blocked! To proceed is necessary '
                      'fill the following fields:\n %s')
        for item in self:
            if item.payment_mode_id and item.payment_mode_id.boleto_type != '':

                error += item.company_id.validate()
                error += item.commercial_partner_id.validate()

                # if item.number and len(item.number) > 12:
                # error += u'Numeração da fatura deve ser menor que 12 ' + \
                # 'caracteres quando usado boleto\n'
                # print(item.number)

                if len(error) > 0:
                    raise UserError(msg_error % error)
        return res

    @api.multi
    def action_register_boleto(self):
        if self.state in ('draft', 'cancel'):
            raise UserError(
                'Fatura provisória ou cancelada não permite emitir boleto')
        self = self.with_context({'origin_model': 'account.invoice'})
        # return self.env['report'].get_action(self.id, 'br_boleto.report.print')
        return self.env.ref('br_boleto.report.print').report_action(self)
