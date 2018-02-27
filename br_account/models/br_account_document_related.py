# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons.br_base.tools import fiscal
from odoo.exceptions import UserError


class AccountDocumentRelated(models.Model):
    _name = 'br_account.document.related'

    invoice_id = fields.Many2one('account.invoice',
                                 string='Documento Fiscal',
                                 ondelete='cascade')

    invoice_related_id = fields.Many2one('account.invoice',
                                         string='Documento Fiscal',
                                         ondelete='cascade')

    document_type = fields.Selection([('nf', 'NF'),
                                      ('nfe', 'NF-e'),
                                      ('cte', 'CT-e'),
                                      ('nfrural', 'NF Produtor'),
                                      ('cf', 'Cupom Fiscal')],
                                     string='Tipo Documento',
                                     required=True)

    access_key = fields.Char('Chave de Acesso', size=44)

    serie = fields.Char('Série', size=12)

    internal_number = fields.Char('Número', size=32)

    state_id = fields.Many2one('res.country.state',
                               string='Estado',
                               domain="[('country_id.code', '=', 'BR')]")

    cnpj_cpf = fields.Char('CNPJ/CPF', size=18)

    cpfcnpj_type = fields.Selection([('cpf', 'CPF'),
                                     ('cnpj', 'CNPJ')],
                                    string='Tipo Doc.',
                                    default='cnpj')

    inscr_est = fields.Char('Inscr. Estadual/RG', size=16)

    date = fields.Date('Data')

    fiscal_document_id = fields.Many2one('br_account.fiscal.document',
                                         string='Documento')

    @api.one
    @api.constrains('cnpj_cpf')
    def _check_cnpj_cpf(self):
        check_cnpj_cpf = True
        if self.cnpj_cpf:
            if self.cpfcnpj_type == 'cnpj':
                if not fiscal.validate_cnpj(self.cnpj_cpf):
                    check_cnpj_cpf = False
            elif not fiscal.validate_cpf(self.cnpj_cpf):
                check_cnpj_cpf = False
        if not check_cnpj_cpf:
            raise UserError('CNPJ/CPF do documento relacionado é invalido!')

    @api.one
    @api.constrains('inscr_est')
    def _check_ie(self):
        check_ie = True
        if self.inscr_est:
            uf = self.state_id and self.state_id.code.lower() or ''
            try:
                mod = __import__('odoo.addons.br_base.tools.fiscal',
                                 globals(), locals(), 'fiscal')

                validate = getattr(mod, 'validate_ie_%s' % uf)
                if not validate(self.inscr_est):
                    check_ie = False
            except AttributeError:
                if not fiscal.validate_ie_param(uf, self.inscr_est):
                    check_ie = False
        if not check_ie:
            raise UserError(
                'Inscrição Estadual do documento fiscal inválida!')

    @api.onchange('invoice_related_id')
    def onchange_invoice_related_id(self):
        if not self.invoice_related_id:
            return
        inv_id = self.invoice_related_id
        if not inv_id.fiscal_document_id:
            return

        if inv_id.fiscal_document_id.code == '55':
            self.document_type = 'nfe'
        elif inv_id.fiscal_document_id.code == '04':
            self.document_type = 'nfrural'
        elif inv_id.fiscal_document_id.code == '57':
            self.document_type = 'cte'
        elif inv_id.fiscal_document_id.code in ('2B', '2C', '2D'):
            self.document_type = 'cf'
        else:
            self.document_type = 'nf'

        if inv_id.fiscal_document_id.code in ('55', '57'):
            self.serie = False
            self.internal_number = False
            self.state_id = False
            self.cnpj_cpf = False
            self.cpfcnpj_type = False
            self.date = False
            self.fiscal_document_id = False
            self.inscr_est = False
