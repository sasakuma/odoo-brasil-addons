# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import copy
from datetime import datetime, timedelta
import dateutil.relativedelta as relativedelta
from odoo.exceptions import UserError
from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

STATE = {'edit': [('readonly', False)]}


class InvoiceElectronic(models.Model):
    _name = 'invoice.electronic'

    _inherit = ['mail.thread']

    code = fields.Char(
        u'Código', size=100, required=True, readonly=True, states=STATE)
    name = fields.Char(
        u'Nome', size=100, required=True, readonly=True, states=STATE)
    company_id = fields.Many2one(
        'res.company', u'Empresa', readonly=True, states=STATE)
    state = fields.Selection(
        [('draft', u'Provisório'),
         ('edit', 'Editar'),
         ('error', 'Erro'),
         ('done', 'Enviado'),
         ('cancel', 'Cancelado')],
        string=u'State', default='draft', readonly=True, states=STATE)
    tipo_operacao = fields.Selection(
        [('entrada', 'Entrada'),
         ('saida', u'Saída')],
        string=u'Tipo de Operação', readonly=True, states=STATE)
    model = fields.Selection(
        [('55', '55 - NFe'),
         ('65', '65 - NFCe'),
         ('001', 'NFS-e - Nota Fiscal Paulistana'),
         ('002', 'NFS-e - Provedor GINFES'),
         ('008', 'NFS-e - Provedor SIMPLISS'),
         ('009', 'NFS-e - Provedor SUSESU')],
        string=u'Modelo', readonly=True, states=STATE)
    serie = fields.Many2one(
        'br_account.document.serie', string=u'Série',
        readonly=True, states=STATE)
    numero = fields.Integer(
        string=u'Número', readonly=True, states=STATE)
    numero_controle = fields.Integer(
        string=u'Número de Controle', readonly=True, states=STATE)
    data_emissao = fields.Datetime(
        string=u'Data emissão', readonly=True, states=STATE)
    data_fatura = fields.Datetime(
        string=u'Data Entrada/Saída', readonly=True, states=STATE)
    data_autorizacao = fields.Char(
        string=u'Data de autorização', size=30, readonly=True, states=STATE)
    ambiente = fields.Selection(
        [('homologacao', u'Homologação'),
         ('producao', u'Produção')],
        string=u'Ambiente', readonly=True, states=STATE)
    finalidade_emissao = fields.Selection(
        [('1', u'1 - Normal'),
         ('2', u'2 - Complementar'),
         ('3', u'3 - Ajuste'),
         ('4', u'4 - Devolução')],
        string=u'Finalidade', help=u"Finalidade da emissão de NFe",
        readonly=True, states=STATE)
    invoice_id = fields.Many2one(
        'account.invoice', string='Fatura', readonly=True, states=STATE)
    partner_id = fields.Many2one(
        'res.partner', string='Parceiro', readonly=True, states=STATE)
    commercial_partner_id = fields.Many2one(
        'res.partner', string='Commercial Entity',
        related='partner_id.commercial_partner_id', store=True)
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Entrega', readonly=True, states=STATE)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Forma pagamento',
        readonly=True, states=STATE)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string=u'Posição Fiscal',
        readonly=True, states=STATE)
    electronic_item_ids = fields.One2many(
        'invoice.electronic.item', 'invoice_electronic_id', string="Linhas",
        readonly=True, states=STATE)
    electronic_event_ids = fields.One2many(
        'invoice.electronic.event', 'invoice_electronic_id', string="Eventos",
        readonly=True, states=STATE)
    valor_bruto = fields.Monetary(
        string=u'Total Produtos', readonly=True, states=STATE)
    valor_frete = fields.Monetary(
        string=u'Total Frete', readonly=True, states=STATE)
    valor_seguro = fields.Monetary(
        string=u'Total Seguro', readonly=True, states=STATE)
    valor_desconto = fields.Monetary(
        string=u'Total Desconto', readonly=True, states=STATE)
    valor_despesas = fields.Monetary(
        string=u'Total Despesas', readonly=True, states=STATE)
    valor_bc_icms = fields.Monetary(
        string=u"Base de Cálculo ICMS", readonly=True, states=STATE)
    valor_icms = fields.Monetary(
        string=u"Total do ICMS", readonly=True, states=STATE)
    valor_icms_deson = fields.Monetary(
        string=u'ICMS Desoneração', readonly=True, states=STATE)
    valor_bc_icmsst = fields.Monetary(
        string=u'Total Base ST', help=u"Total da base de cálculo do ICMS ST",
        readonly=True, states=STATE)
    valor_icmsst = fields.Monetary(
        string=u'Total ST', readonly=True, states=STATE)
    valor_ii = fields.Monetary(
        string=u'Total II', readonly=True, states=STATE)
    valor_ipi = fields.Monetary(
        string=u"Total IPI", readonly=True, states=STATE)
    valor_pis = fields.Monetary(
        string=u"Total PIS", readonly=True, states=STATE)
    valor_cofins = fields.Monetary(
        string=u"Total COFINS", readonly=True, states=STATE)
    valor_estimado_tributos = fields.Monetary(
        string=u"Tributos Estimados", readonly=True, states=STATE)

    valor_servicos = fields.Monetary(
        string=u"Total Serviços", readonly=True, states=STATE)
    valor_bc_issqn = fields.Monetary(
        string=u"Base ISS", readonly=True, states=STATE)
    valor_issqn = fields.Monetary(
        string=u"Total ISS", readonly=True, states=STATE)
    valor_pis_servicos = fields.Monetary(
        string=u"Total PIS Serviços", readonly=True, states=STATE)
    valor_cofins_servicos = fields.Monetary(
        string=u"Total Cofins Serviço", readonly=True, states=STATE)

    valor_retencao_issqn = fields.Monetary(
        string=u"Retenção ISSQN", readonly=True, states=STATE)
    valor_retencao_pis = fields.Monetary(
        string=u"Retenção PIS", readonly=True, states=STATE)
    valor_retencao_cofins = fields.Monetary(
        string=u"Retenção COFINS", readonly=True, states=STATE)
    valor_bc_irrf = fields.Monetary(
        string=u"Base de Cálculo IRRF", readonly=True, states=STATE)
    valor_retencao_irrf = fields.Monetary(
        string=u"Retenção IRRF", readonly=True, states=STATE)
    valor_bc_csll = fields.Monetary(
        string=u"Base de Cálculo CSLL", readonly=True, states=STATE)
    valor_retencao_csll = fields.Monetary(
        string=u"Retenção CSLL", readonly=True, states=STATE)
    valor_bc_inss = fields.Monetary(
        string=u"Base de Cálculo INSS", readonly=True, states=STATE)
    valor_retencao_inss = fields.Monetary(
        string=u"Retenção INSS", help=u"Retenção Previdência Social",
        readonly=True, states=STATE)

    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")
    valor_final = fields.Monetary(
        string=u'Valor Final', readonly=True, states=STATE)

    informacoes_legais = fields.Text(
        string=u'Informações legais', readonly=True, states=STATE)
    informacoes_complementares = fields.Text(
        string=u'Informações complementares', readonly=True, states=STATE)

    codigo_retorno = fields.Char(
        string=u'Código Retorno', readonly=True, states=STATE)
    mensagem_retorno = fields.Char(
        string=u'Mensagem Retorno', readonly=True, states=STATE)
    numero_nfe = fields.Char(
        string="Numero Formatado NFe", readonly=True, states=STATE)

    xml_to_send = fields.Binary(string="Xml a Enviar", readonly=True)
    xml_to_send_name = fields.Char(
        string="Nome xml a ser enviado", size=100, readonly=True)

    email_sent = fields.Boolean(string="Email enviado", default=False,
                                readonly=True, states=STATE)

    def _create_attachment(self, prefix, event, data):
        file_name = '%s-%s.xml' % (
            prefix, datetime.now().strftime('%Y-%m-%d-%H-%M'))
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'invoice.electronic',
                'res_id': event.id
            })

    @api.multi
    def _hook_validation(self):
        """
            Override this method to implement the validations specific
            for the city you need
            @returns list<string> errors
        """
        errors = []
        if not self.serie.fiscal_document_id:
            errors.append(u'Nota Fiscal - Tipo de documento fiscal')
        if not self.serie.internal_sequence_id:
            errors.append(u'Nota Fiscal - Número da nota fiscal, \
                          a série deve ter uma sequencia interna')

        # Emitente
        if not self.company_id.nfe_a1_file:
            errors.append(u'Emitente - Certificado Digital')
        if not self.company_id.nfe_a1_password:
            errors.append(u'Emitente - Senha do Certificado Digital')
        if not self.company_id.partner_id.legal_name:
            errors.append(u'Emitente - Razão Social')
        if not self.company_id.partner_id.cnpj_cpf:
            errors.append(u'Emitente - CNPJ/CPF')
        if not self.company_id.partner_id.street:
            errors.append(u'Emitente / Endereço - Logradouro')
        if not self.company_id.partner_id.number:
            errors.append(u'Emitente / Endereço - Número')
        if not self.company_id.partner_id.zip or len(
                re.sub(r"\D", "", self.company_id.partner_id.zip)) != 8:
            errors.append(u'Emitente / Endereço - CEP')
        if not self.company_id.partner_id.state_id:
            errors.append(u'Emitente / Endereço - Estado')
        else:
            if not self.company_id.partner_id.state_id.ibge_code:
                errors.append(u'Emitente / Endereço - Cód. do IBGE do estado')
            if not self.company_id.partner_id.state_id.name:
                errors.append(u'Emitente / Endereço - Nome do estado')

        if not self.company_id.partner_id.city_id:
            errors.append(u'Emitente / Endereço - município')
        else:
            if not self.company_id.partner_id.city_id.name:
                errors.append(u'Emitente / Endereço - Nome do município')
            if not self.company_id.partner_id.city_id.ibge_code:
                errors.append(u'Emitente/Endereço - Cód. do IBGE do município')

        if not self.company_id.partner_id.country_id:
            errors.append(u'Emitente / Endereço - país')
        else:
            if not self.company_id.partner_id.country_id.name:
                errors.append(u'Emitente / Endereço - Nome do país')
            if not self.company_id.partner_id.country_id.bc_code:
                errors.append(u'Emitente / Endereço - Código do BC do país')

        partner = self.partner_id.commercial_partner_id
        company = self.company_id
        # Destinatário
        if partner.is_company and not partner.legal_name:
            errors.append(u'Destinatário - Razão Social')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.cnpj_cpf:
                errors.append(u'Destinatário - CNPJ/CPF')

        if not partner.street:
            errors.append(u'Destinatário / Endereço - Logradouro')

        if not partner.number:
            errors.append(u'Destinatário / Endereço - Número')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.zip or len(
                    re.sub(r"\D", "", partner.zip)) != 8:
                errors.append(u'Destinatário / Endereço - CEP')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.state_id:
                errors.append(u'Destinatário / Endereço - Estado')
            else:
                if not partner.state_id.ibge_code:
                    errors.append(u'Destinatário / Endereço - Código do IBGE \
                                  do estado')
                if not partner.state_id.name:
                    errors.append(u'Destinatário / Endereço - Nome do estado')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.city_id:
                errors.append(u'Destinatário / Endereço - Município')
            else:
                if not partner.city_id.name:
                    errors.append(u'Destinatário / Endereço - Nome do \
                                  município')
                if not partner.city_id.ibge_code:
                    errors.append(u'Destinatário / Endereço - Código do IBGE \
                                  do município')

        if not partner.country_id:
            errors.append(u'Destinatário / Endereço - País')
        else:
            if not partner.country_id.name:
                errors.append(u'Destinatário / Endereço - Nome do país')
            if not partner.country_id.bc_code:
                errors.append(u'Destinatário / Endereço - Cód. do BC do país')

        # produtos
        for eletr in self.electronic_item_ids:
            if eletr.product_id:
                if not eletr.product_id.default_code:
                    errors.append(
                        u'Prod: %s - Código do produto' % (
                            eletr.product_id.name))
        return errors

    @api.multi
    def _compute_legal_information(self):
        fiscal_ids = self.invoice_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == 'fiscal')
        obs_ids = self.invoice_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == 'observacao')

        prod_obs_ids = self.env['br_account.fiscal.observation'].browse()
        for item in self.invoice_id.invoice_line_ids:
            prod_obs_ids |= item.product_id.fiscal_observation_ids

        fiscal_ids |= prod_obs_ids.filtered(lambda x: x.tipo == 'fiscal')
        obs_ids |= prod_obs_ids.filtered(lambda x: x.tipo == 'observacao')

        fiscal = self._compute_msg(fiscal_ids) + (
            self.invoice_id.fiscal_comment or '')
        observacao = self._compute_msg(obs_ids) + (
            self.invoice_id.comment or '')

        self.informacoes_legais = fiscal
        self.informacoes_complementares = observacao

    def _compute_msg(self, observation_ids):
        from jinja2.sandbox import SandboxedEnvironment
        mako_template_env = SandboxedEnvironment(
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="${",
            variable_end_string="}",
            comment_start_string="<%doc>",
            comment_end_string="</%doc>",
            line_statement_prefix="%",
            line_comment_prefix="##",
            trim_blocks=True,  # do not output newline after
            autoescape=True,  # XML/HTML automatic escaping
        )
        mako_template_env.globals.update({
            'str': str,
            'datetime': datetime,
            'len': len,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'filter': filter,
            'reduce': reduce,
            'map': map,
            'round': round,
            'cmp': cmp,
            # dateutil.relativedelta is an old-style class and cannot be
            # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
            # is needed, apparently.
            'relativedelta': lambda *a, **kw: relativedelta.relativedelta(
                *a, **kw),
        })
        mako_safe_env = copy.copy(mako_template_env)
        mako_safe_env.autoescape = False

        result = ''
        for item in observation_ids:
            if item.document_id and item.document_id.code != self.model:
                continue
            template = mako_safe_env.from_string(tools.ustr(item.message))
            variables = {
                'user': self.env.user,
                'ctx': self._context,
                'invoice': self.invoice_id,
            }
            render_result = template.render(variables)
            result += render_result + '\n'
        return result

    @api.multi
    def validate_invoice(self):
        self.ensure_one()
        errors = self._hook_validation()
        if len(errors) > 0:
            msg = u"\n".join(
                [u"Por favor corrija os erros antes de prosseguir"] + errors)
            raise UserError(msg)

    @api.multi
    def action_post_validate(self):
        self._compute_legal_information()

    @api.multi
    def action_print_einvoice_report(self):
        action = {
            "type": "ir.actions.act_url",
            "url": '',
            "target": "_blank",
        }
        return action

    @api.multi
    def _prepare_electronic_invoice_item(self, item, invoice):
        return {}

    @api.multi
    def _prepare_electronic_invoice_values(self):
        return {}

    @api.multi
    def action_send_electronic_invoice(self):
        for item in self:
            if item.state == 'done':
                raise UserError(u'Documento Eletrônico já enviado - '
                                u'Proibido reenviar')

    @api.multi
    def _on_success(self):
        pass

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        pass

    @api.multi
    def action_back_to_draft(self):
        self.state = 'draft'

    @api.multi
    def action_edit_edoc(self):
        self.state = 'edit'

    def can_unlink(self):
        if self.state not in ('done', 'cancel'):
            return True
        return False

    @api.multi
    def unlink(self):
        for item in self:
            if not item.can_unlink():
                raise UserError(
                    u'Documento Eletrônico enviado - Proibido excluir')
        super(InvoiceElectronic, self).unlink()

    def log_exception(self, exc):
        self.codigo_retorno = -1
        self.mensagem_retorno = exc.message

    def _get_state_to_send(self):
        return ('draft',)

    @api.multi
    def cron_send_nfe(self):
        inv_obj = self.env['invoice.electronic'].with_context({
            'lang': self.env.user.lang, 'tz': self.env.user.tz})
        states = self._get_state_to_send()
        nfes = inv_obj.search([('state', 'in', states)])
        for item in nfes:
            try:
                item.action_send_electronic_invoice()
            except Exception as e:
                item.log_exception(e)

    def _find_attachment_ids_email(self):
        return []

    @api.multi
    def send_email_nfe(self):
        mail = self.env.user.company_id.nfe_email_template
        if not mail:
            raise UserError('Modelo de email padrão não configurado')
        atts = self._find_attachment_ids_email()

        if atts and len(atts):
            mail.attachment_ids = [(6, 0, atts)]
        mail.send_mail(self.invoice_id.id)

    @api.multi
    def send_email_nfe_queue(self):
        after = datetime.now() + timedelta(days=-1)
        nfe_queue = self.env['invoice.electronic'].search(
            [('data_emissao', '>=', after.strftime(DATETIME_FORMAT)),
             ('email_sent', '=', False),
             ('state', '=', 'done')], limit=5)
        for nfe in nfe_queue:
            nfe.send_email_nfe()
            nfe.email_sent = True
