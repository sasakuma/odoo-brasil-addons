# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    webservice_nfse = fields.Selection(selection_add=[
        ('nfse_paulistana', 'Nota Fiscal Paulistana'),
    ])

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        # res['codigo_servico_paulistana'] = \
        #     line.service_type_id.codigo_servico_paulistana
        res['codigo_servico_paulistana'] = \
            line.fiscal_position_id.service_type_id.codigo_servico_paulistana
        return res

    def action_preview_danfse(self):
        action = super(AccountInvoice, self).action_preview_danfse()
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])

        if self.invoice_model == '001' \
                and self.webservice_nfse == 'nfse_paulistana':
            report = \
                'br_nfse_paulistana.main_template_br_nfse_danfe_paulistana'

        # elif self.invoice_model == '001' \
        #         and self.webservice_nfse == 'nfse_simpliss':
        #    report = 'br_nfse.main_template_br_nfse_danfe_simpliss_piracicaba'

        action = self.env['report'].get_action(docs.ids, report)
        action['report_type'] = 'qweb-html'
        return action

