# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.exceptions import UserError


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

        if self.invoice_model == '001' \
                and self.webservice_nfse == 'nfse_paulistana':

            if self.company_id.report_nfse_id:
                report = self.company_id.report_nfse_id.report_name

                # Apenas documentos eletronicos que estao como 'draft' (RPS)
                # ou ja foram enviados 'done' (são NFSe)
                docs = self.env['invoice.electronic'].search([
                    ('invoice_id', '=', self.id),
                    ('state', 'in', ['draft', 'done']),
                ])

                if not docs:
                    # Se não encontrarmos nenhum documento eletronico enviado
                    # ou provisorio, imprimimos um documento eletronico
                    # que foram cancelados
                    docs = self.env['invoice.electronic'].search([
                        ('invoice_id', '=', self.id),
                        ('state', 'in', ['cancel']),
                    ])

                action = self.env['report'].get_action(docs.ids, report)
                action['report_type'] = 'qweb-pdf'

            else:
                raise UserError(
                    u'Não existe um template de relatorio para NFSe '
                    u'selecionado para a empresa emissora desta Fatura. '
                    u'Por favor, selecione um template no cadastro da empresa')

        return action
