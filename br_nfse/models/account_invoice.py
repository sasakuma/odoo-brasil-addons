# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _compute_nfse_number(self):
        for invoice in self:
            docs = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])
            if docs:
                invoice.nfse_number = docs[0].numero
                invoice.nfse_exception_number = docs[0].numero
                invoice.nfse_exception = (docs[0].state in ('error', 'denied'))
                invoice.sending_nfse = docs[0].state == 'draft'
                invoice.nfse_status = '%s - %s' % (docs[0].codigo_retorno,
                                                   docs[0].mensagem_retorno)

    ambiente_nfse = fields.Selection(string='Ambiente NFSe',
                                     related='company_id.tipo_ambiente_nfse',
                                     readonly=True)

    webservice_nfse = fields.Selection([],
                                       readonly=True,
                                       states={'draft': [('readonly', False)]},
                                       string='Webservice NFSe')

    sending_nfse = fields.Boolean(string='Enviando NFSe?',
                                  compute='_compute_nfse_number')

    nfse_exception = fields.Boolean(string='Problemas na NFSe?',
                                    compute='_compute_nfse_number')

    nfse_status = fields.Char(string='Mensagem NFSe',
                              compute='_compute_nfse_number')

    nfse_number = fields.Integer(string=u'Número NFSe',
                                 compute='_compute_nfse_number')

    nfse_exception_number = fields.Integer(string=u'Número NFSe',
                                           compute='_compute_nfse_number')

    @api.onchange('fiscal_document_id')
    def _onchange_fiscal_document_id(self):
        super(AccountInvoice, self)._onchange_fiscal_document_id()

        # Se o documento fiscal dor NFSe, capturamos a webservice configurado
        # no cadastro da empresa e o utilizamos, caso contrário apagamos o
        # valor contido no campo 'webservice_nfse' para que, posteriormente,
        # possamos utilizar o mesmo como filtro

        fiscal_document_nfse = self.env.ref('br_nfse.fiscal_document_001')

        # Definimos o ambiente da NFSe apenas se o tipo de fatura for NFSe
        if self.fiscal_document_id.id == fiscal_document_nfse.id:
            company = self.env['res.company'].browse(
                self.env.user.company_id.id)
            self.webservice_nfse = company.webservice_nfse
        else:
            self.webservice_nfse = False

    # def _prepare_edoc_item_vals(self, line):
    #     res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
    #     # res['codigo_servico_paulistana'] = \
    #     #     line.service_type_id.codigo_servico_paulistana
    #     res['codigo_servico_paulistana'] = \
    #         line.fiscal_position_id.service_type_id.codigo_servico_paulistana
    #     return res

    def _prepare_edoc_vals(self, invoice):
        res = super(AccountInvoice, self)._prepare_edoc_vals(invoice)

        # Indica que a fatura é uma Nota Fiscal Eletronica de Serviço
        fiscal_document_nfse = self.env.ref('br_nfse.fiscal_document_001')

        # Definimos o ambiente da NFSe apenas se o tipo de fatura for NFSe
        if self.fiscal_document_id.id == fiscal_document_nfse.id:
            res['ambiente'] = ('homologacao' if invoice.ambiente_nfse == '2'
                               else 'producao')
            res['webservice_nfse'] = self.webservice_nfse
        return res

    def action_preview_danfse(self):
        docs = self.env['invoice.electronic'].search(
            [('invoice_id', '=', self.id)])
        if not docs:
            raise UserError(u'Não existe um E-Doc relacionado à esta fatura')

        # if self.invoice_model == '009':
        #     if docs[0].state != 'done':
        #         raise UserError('Nota Fiscal na fila de envio. Aguarde!')
        #     return {
        #         "type": "ir.actions.act_url",
        #         "url": docs[0].url_danfe,
        #         "target": "_blank",
        #     }

        action = {
            "type": "ir.actions.act_url",
            "url": '',
            "target": "_blank",
        }
        return action
