# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    @api.multi
    def _load_template(self, company, code_digits=None,
                       transfer_account_id=None, account_ref=None,
                       taxes_ref=None):
        acc_ref, tax_ref = super(AccountChartTemplate, self)._load_template(
            company, code_digits, transfer_account_id, account_ref, taxes_ref)

        tax_tmpl_obj = self.env['account.tax.template']
        tax_obj = self.env['account.tax']
        for key, value in tax_ref.items():
            tax_tmpl_id = tax_tmpl_obj.browse(key)
            tax_obj.browse(value).write({
                'deduced_account_id': acc_ref.get(
                    tax_tmpl_id.deduced_account_id.id, False),
                'refund_deduced_account_id': acc_ref.get(
                    tax_tmpl_id.refund_deduced_account_id.id, False)
            })
        return acc_ref, tax_ref
