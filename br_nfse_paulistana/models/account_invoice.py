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
        res['codigo_servico_paulistana'] = \
            line.fiscal_position_id.service_type_id.codigo_servico_paulistana
        return res
