# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _compute_nfse_number(self):
        for invoice in self:
            docs = self.env['invoice.electronic'].search(
                [('invoice_id', '=', invoice.id)])

            if docs:
                invoice.nfse_number = docs[-1].numero
                invoice.nfse_exception_number = docs[-1].numero
                invoice.nfse_exception = (docs[-1].state in ('error', 'denied'))
                invoice.sending_nfse = docs[-1].state == 'draft'
                invoice.nfse_status = '%s - %s' % (docs[-1].codigo_retorno,
                                                   docs[-1].mensagem_retorno)

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

    nfse_number = fields.Integer(string='Número NFSe',
                                 compute='_compute_nfse_number')

    nfse_exception_number = fields.Integer(string='Número NFSe',
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

    @api.multi
    def action_print_danfse(self):

        # Apenas documentos eletronicos que estao como 'draft' (RPS)
        # ou ja foram enviados 'done' (são NFSe)
        docs = self.env['invoice.electronic'].search([
            ('invoice_id', 'in', self.ids),
            ('model', '=', '001'),
            ('state', 'in', ['done', 'paid']),
        ])

        if not docs:
            # Se não encontrarmos nenhum documento eletronico enviado
            # ou provisorio, imprimimos um documento eletronico
            # que foram cancelados
            docs = self.env['invoice.electronic'].search([
                ('invoice_id', 'in', self.ids),
                ('model', '=', '001'),
                ('state', 'in', ['cancel']),
            ])

        return docs.action_print_einvoice_report()
