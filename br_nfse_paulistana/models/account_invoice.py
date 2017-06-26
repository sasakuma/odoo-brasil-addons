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
        # if not docs:
        #     raise UserError(u'Não existe um E-Doc relacionado à esta fatura')
        #
        # if self.invoice_model == '009':
        #     if docs[0].state != 'done':
        #         raise UserError('Nota Fiscal na fila de envio. Aguarde!')
        #     return {
        #         "type": "ir.actions.act_url",
        #         "url": docs[0].url_danfe,
        #         "target": "_blank",
        #     }
        #
        # report = ''

        docs[0].observacao_nfse = self._get_nfse_observation_text(docs[0])

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

    def _get_nfse_observation_text(self, docm):

        observacao_nfse = ''

        aux = []

        if self.invoice_model == '001':
            observacao_nfse = u'# Esta NFS-e foi emitida com respaldo na ' \
                              u'Lei nº 14.097/2005; '

            aux.append(observacao_nfse)

            if docm.state == 'done':
                if docm.company_id.fiscal_type == '1':
                    observacao_nfse = u'# Documento emitido por ME ou EPP ' \
                                      u'optante pelo Simples Nacional; '

                    aux.append(observacao_nfse)

                observacao_nfse = u'# Esta NFS-e substitui o RPS Nº %d ' \
                                  u'Série %s, ' \
                                  u'emitido em %s; ' % (docm.numero,
                                                        docm.serie.code,
                                                        docm.data_emissao[:10])

                aux.append(observacao_nfse)

            observacao_nfse = ''

            for index, value in enumerate(aux):
                observacao_nfse += value.replace('#', '(%d)' % (index + 1))

        return observacao_nfse
