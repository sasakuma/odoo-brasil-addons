# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2017 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import copy

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare
from odoo.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    STATES = {
        'draft': [('readonly', False)],
    }

    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'invoice_line_ids.price_total',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids
        self.total_tax = sum(l.price_tax for l in lines)
        self.icms_base = sum(l.icms_base_calculo for l in lines)
        self.icms_value = sum(l.icms_valor for l in lines)
        self.icms_st_base = sum(l.icms_st_base_calculo for l in lines)
        self.icms_st_value = sum(l.icms_st_valor for l in lines)
        self.valor_icms_uf_remet = sum(l.icms_uf_remet for l in lines)
        self.valor_icms_uf_dest = sum(l.icms_uf_dest for l in lines)
        self.valor_icms_fcp_uf_dest = sum(l.icms_fcp_uf_dest for l in lines)
        self.issqn_base = sum(l.issqn_base_calculo for l in lines)
        self.issqn_value = sum(abs(l.issqn_valor) for l in lines)
        self.ipi_base = sum(l.ipi_base_calculo for l in lines)
        self.ipi_value = sum(l.ipi_valor for l in lines)
        self.pis_base = sum(l.pis_base_calculo for l in lines)
        self.pis_value = sum(abs(l.pis_valor) for l in lines)
        self.cofins_base = sum(l.cofins_base_calculo for l in lines)
        self.cofins_value = sum(abs(l.cofins_valor) for l in lines)
        self.ii_value = sum(l.ii_valor for l in lines)
        self.csll_base = sum(l.csll_base_calculo for l in lines)
        self.csll_value = sum(abs(l.csll_valor) for l in lines)
        self.irrf_base = sum(l.irrf_base_calculo for l in lines)
        self.irrf_value = sum(abs(l.irrf_valor) for l in lines)
        self.inss_base = sum(l.inss_base_calculo for l in lines)
        self.inss_value = sum(abs(l.inss_valor) for l in lines)

        # Retenções
        self.issqn_retention = sum(
            abs(l.issqn_valor) if l.issqn_valor < 0 else 0.0 for l in lines)
        self.pis_retention = sum(
            abs(l.pis_valor) if l.pis_valor < 0 else 0.0 for l in lines)
        self.cofins_retention = sum(
            abs(l.cofins_valor) if l.cofins_valor < 0 else 0.0 for l in lines)
        self.csll_retention = sum(
            abs(l.csll_valor) if l.csll_valor < 0 else 0 for l in lines)
        self.irrf_retention = sum(
            abs(l.irrf_valor) if l.irrf_valor < 0 else 0.0 for l in lines)
        self.inss_retention = sum(
            abs(l.inss_valor) if l.inss_valor < 0 else 0.0 for l in lines)

        self.total_bruto = sum(l.valor_bruto for l in lines)
        self.total_desconto = sum(l.valor_desconto for l in lines)
        self.total_tributos_federais = sum(
            l.tributos_estimados_federais for l in lines)
        self.total_tributos_estaduais = sum(
            l.tributos_estimados_estaduais for l in lines)
        self.total_tributos_municipais = sum(
            l.tributos_estimados_municipais for l in lines)
        self.total_tributos_estimados = sum(
            l.tributos_estimados for l in lines)
        # TOTAL
        self.amount_total = \
            self.total_bruto - self.total_desconto + self.total_tax
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = self.amount_total * sign
        self.amount_total_signed = self.amount_total * sign

    total_tax = fields.Float(string='Impostos ( + )',
                             readonly=True,
                             compute='_compute_amount',
                             digits=dp.get_precision('Account'),
                             store=True)

    parcel_ids = fields.One2many(comodel_name='br_account.invoice.parcel',
                                 inverse_name='invoice_id',
                                 readonly=True,
                                 states=STATES,
                                 string='Parcelas')

    move_ids = fields.One2many('account.move',
                               inverse_name='invoice_id',
                               readonly=True,
                               string='Account Move')

    issuer = fields.Selection([('0', 'Terceiros'),
                               ('1', 'Emissão própria')],
                              string='Emitente',
                              default='0',
                              readonly=True,
                              states=STATES)

    vendor_number = fields.Char(string='Número NF Entrada',
                                size=18,
                                readonly=True,
                                states=STATES,
                                help='Número da Nota Fiscal do Fornecedor')

    vendor_serie = fields.Char(string='Série NF Entrada',
                               size=12,
                               help="Série do número da Nota Fiscal do "
                                    "Fornecedor")

    document_serie_id = fields.Many2one('br_account.document.serie',
                                        string='Série',
                                        readonly=True,
                                        states=STATES)

    fiscal_document_id = fields.Many2one('br_account.fiscal.document',
                                         string='Documento',
                                         readonly=True,
                                         states=STATES)

    invoice_model = fields.Char(string='Modelo de Fatura',
                                related='fiscal_document_id.code',
                                readonly=True)

    pre_invoice_date = fields.Date(string='Data da Pré-Fatura',
                                   required=True,
                                   copy=False,
                                   default=fields.Date.today)

    cancel_invoice_date = fields.Date(string='Data da Cancelamento',
                                      readonly=True,
                                      copy=False)

    date_invoice = fields.Date(copy=False)

    internal_number = fields.Integer(string='Invoice Number',
                                     readonly=True,
                                     copy=False,
                                     group_operator=None,
                                     states={'draft': [('readonly', False)]},
                                     help="""Unique number of the invoice,
                                     computed automatically when the invoice
                                     is created.""")

    number_backup = fields.Char(copy=False, 
                                string='Backup do numero do pedido')

    is_electronic = fields.Boolean(related='fiscal_document_id.electronic',
                                   type='boolean',
                                   store=True,
                                   string='Eletrônico',
                                   readonly=True,
                                   oldname='is_eletronic')

    fiscal_document_related_ids = fields.One2many(
        'br_account.document.related',
        'invoice_id',
        string='Documento Fiscal Relacionado',
        readonly=True,
        states=STATES)

    fiscal_observation_ids = fields.Many2many('br_account.fiscal.observation',
                                              string='Observações Fiscais',
                                              readonly=True,
                                              states=STATES)

    fiscal_comment = fields.Text('Observação Fiscal',
                                 readonly=True,
                                 states=STATES)

    total_bruto = fields.Float(string='Total Bruto ( = )',
                               store=True,
                               digits=dp.get_precision('Account'),
                               compute='_compute_amount')

    total_desconto = fields.Float(string='Desconto ( - )',
                                  store=True,
                                  digits=dp.get_precision('Account'),
                                  compute='_compute_amount')

    icms_base = fields.Float(string='Base ICMS',
                             store=True,
                             compute='_compute_amount',
                             digits=dp.get_precision('Account'))

    icms_value = fields.Float(string='Valor ICMS',
                              digits=dp.get_precision('Account'),
                              compute='_compute_amount',
                              store=True)

    icms_st_base = fields.Float(string='Base ICMS ST',
                                store=True,
                                compute='_compute_amount',
                                digits=dp.get_precision('Account'))

    icms_st_value = fields.Float(string='Valor ICMS ST',
                                 store=True,
                                 compute='_compute_amount',
                                 digits=dp.get_precision('Account'))

    valor_icms_fcp_uf_dest = fields.Float(string='Total ICMS FCP',
                                          store=True,
                                          compute='_compute_amount',
                                          help='Total total do ICMS relativo'
                                               ' Fundo de Combate à Pobreza '
                                               '(FCP) da UF de destino')

    valor_icms_uf_dest = fields.Float(string='ICMS Destino',
                                      store=True,
                                      compute='_compute_amount',
                                      help='Valor total do ICMS Interestadual'
                                           ' para a UF de destino')

    valor_icms_uf_remet = fields.Float(string='ICMS Remetente',
                                       store=True,
                                       compute='_compute_amount',
                                       help='Valor total do ICMS Interestadual'
                                            ' para a UF do Remetente')

    issqn_base = fields.Float(string='Base ISSQN',
                              store=True,
                              digits=dp.get_precision('Account'),
                              compute='_compute_amount')

    issqn_value = fields.Float(string='Valor ISSQN',
                               store=True,
                               digits=dp.get_precision('Account'),
                               compute='_compute_amount')

    issqn_retention = fields.Float(string='ISSQN Retido',
                                   store=True,
                                   digits=dp.get_precision('Account'),
                                   compute='_compute_amount')

    ipi_base = fields.Float(string='Base IPI',
                            store=True,
                            digits=dp.get_precision('Account'),
                            compute='_compute_amount')

    ipi_base_other = fields.Float(string="Base IPI Outras",
                                  store=True,
                                  digits=dp.get_precision('Account'),
                                  compute='_compute_amount')

    ipi_value = fields.Float(string='Valor IPI',
                             store=True,
                             digits=dp.get_precision('Account'),
                             compute='_compute_amount')

    pis_base = fields.Float(string='Base PIS',
                            store=True,
                            digits=dp.get_precision('Account'),
                            compute='_compute_amount')

    pis_value = fields.Float(string='Valor PIS',
                             store=True,
                             digits=dp.get_precision('Account'),
                             compute='_compute_amount')

    pis_retention = fields.Float(string='PIS Retido',
                                 store=True,
                                 digits=dp.get_precision('Account'),
                                 compute='_compute_amount')

    cofins_base = fields.Float(string='Base COFINS',
                               store=True,
                               digits=dp.get_precision('Account'),
                               compute='_compute_amount')

    cofins_value = fields.Float(string='Valor COFINS',
                                store=True,
                                digits=dp.get_precision('Account'),
                                compute='_compute_amount',
                                readonly=True)

    cofins_retention = fields.Float(string='COFINS Retido',
                                    store=True,
                                    digits=dp.get_precision('Account'),
                                    compute='_compute_amount',
                                    readonly=True)

    ii_value = fields.Float(string='Valor II',
                            store=True,
                            digits=dp.get_precision('Account'),
                            compute='_compute_amount')

    csll_base = fields.Float(string='Base CSLL',
                             store=True,
                             digits=dp.get_precision('Account'),
                             compute='_compute_amount')

    csll_value = fields.Float(string='Valor CSLL',
                              store=True,
                              digits=dp.get_precision('Account'),
                              compute='_compute_amount')

    csll_retention = fields.Float(string='CSLL Retido',
                                  store=True,
                                  digits=dp.get_precision('Account'),
                                  compute='_compute_amount')

    irrf_base = fields.Float(string='Base IRRF',
                             store=True,
                             digits=dp.get_precision('Account'),
                             compute='_compute_amount')

    irrf_value = fields.Float(string='Valor IRRF',
                              store=True,
                              digits=dp.get_precision('Account'),
                              compute='_compute_amount')

    irrf_retention = fields.Float(string='IRRF Retido',
                                  store=True,
                                  digits=dp.get_precision('Account'),
                                  compute='_compute_amount')

    inss_base = fields.Float(string='Base INSS',
                             store=True,
                             digits=dp.get_precision('Account'),
                             compute='_compute_amount')

    inss_value = fields.Float(string='Valor INSS',
                              store=True,
                              digits=dp.get_precision('Account'),
                              compute='_compute_amount')

    inss_retention = fields.Float(string='INSS Retido',
                                  store=True,
                                  digits=dp.get_precision('Account'),
                                  compute='_compute_amount')

    total_tributos_federais = fields.Float(string='Total de Tributos Federais',
                                           store=True,
                                           digits=dp.get_precision('Account'),
                                           compute='_compute_amount')

    total_tributos_estaduais = fields.Float(
        string='Total de Tributos Estaduais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    total_tributos_municipais = fields.Float(
        string='Total de Tributos Municipais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    total_tributos_estimados = fields.Float(string='Total de Tributos',
                                            store=True,
                                            digits=dp.get_precision('Account'),
                                            compute='_compute_amount')

    chave_de_acesso = fields.Char(string='Chave de Acesso', size=44)

    @api.onchange('issuer')
    def _onchange_issuer(self):
        if self.issuer == '0' and self.type in ('in_invoice', 'in_refund'):
            self.fiscal_document_id = None
            self.document_serie_id = None

    @api.onchange('fiscal_document_id')
    def _onchange_fiscal_document_id(self):
        series = self.env['br_account.document.serie'].search(
            [('fiscal_document_id', '=', self.fiscal_document_id.id)])
        self.document_serie_id = series and series[0].id or False

    @api.onchange('fiscal_position_id')
    def _onchange_br_account_fiscal_position_id(self):
        if self.fiscal_position_id and self.fiscal_position_id.account_id:
            self.account_id = self.fiscal_position_id.account_id.id

        if self.fiscal_position_id and self.fiscal_position_id.journal_id:
            self.journal_id = self.fiscal_position_id.journal_id

        ob_ids = [x.id for x in self.fiscal_position_id.fiscal_observation_ids]
        self.fiscal_observation_ids = [(6, False, ob_ids)]

        self.fiscal_document_id = self.fiscal_position_id.fiscal_document_id.id
        self.fiscal_comment = self.fiscal_position_id.note

    @api.multi
    def action_move_create(self):
        """Cria lançamento de diario a partir da confirmação da fatura.
        Diferente do mesmo metodo presente no core, este metodo altera
        o comportamento original criando uma account.move para cada
        parcela do sistema e separando assim as account.move.line
        e lançamentos diferentes.
        """

        # O sistema de parcelas sera obrigatorio, entao sempre teremos pelo
        # menos uma parcela. Esse verificacao foi adicionada para manter
        # compatibilidade com os testes do core.
        # O valor 'user_parcel_system' foi adicionado no metodo
        # 'action_br_account_invoice_open'
        if not self.env.context.get('use_parcel_system'):
            return super(AccountInvoice, self).action_move_create()

        account_move = self.env['account.move']

        for inv in self:

            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal '
                                  'related to this invoice.'))

            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))

            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            inv.with_context(ctx).write({
                'date_invoice': fields.Date.context_today(self),
            })

            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and
            #  analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            # create one move line for the total and possibly adjust the other
            # lines amount
            iml = \
                inv.with_context(ctx).compute_invoice_totals(company_currency,
                                                             iml)[2]

            for parcel in inv.parcel_ids:
                # Calculamos a nova data de vencimento baseado na data
                # de validação da faturação, caso a parcela nao esteja
                # marcada como 'data fixa'. A data da parcela também é
                # atualizada
                parcel.update_date_maturity(inv.date_invoice)

                new_iml = copy.deepcopy(iml)
                
                # Itera sobre a lista de imls de receita/despesa para
                # atribuir valor e data de vencimento
                for index, ml in enumerate(new_iml):
                    invl_obj = self.env['account.invoice.line'].browse(
                        ml['invl_id'])
                    signal = -1 if ml['price'] < 0 else 1
                    # Os condicionais abaixo servem para garantir que em caso
                    # de dizima no valor a ser distribuido nas imls, o eventual
                    # residuo deixado pelo arredondamento, seja aplicado a 
                    # ultima das imls
                    if index == len(new_iml) -1:
                        # Lista equivalente a imls anteriores a ultima
                        previous_lines = new_iml[:len(new_iml) - 1]

                        sum_in_previous_lines = sum(
                            l['price'] for l in previous_lines)
                        ml['price'] = round(
                            signal * (parcel.abs_parceling_value - abs(
                                sum_in_previous_lines)), 2)
                    else:
                        ml['price'] = round(
                                signal * parcel.abs_parceling_value * invl_obj.percent_subtotal)
                    ml['date_maturity'] = parcel.date_maturity

                new_iml.append({
                    'type': 'dest',
                    'name': inv.name or '/',
                    'price': parcel.parceling_value,
                    'account_id': inv.account_id.id,
                    'date_maturity': parcel.date_maturity,
                    'amount_currency': parcel.amount_currency,
                    'currency_id': parcel.currency_id.id,
                    'invoice_id': inv.id,
                    'company_id': inv.company_id.id,
                })

                part = self.env['res.partner']._find_accounting_partner(
                    inv.partner_id)

                line = [(0, 0, self.line_get_convert(l, part.id))
                        for l in new_iml]

                line = inv.group_lines(new_iml, line)

                journal = inv.journal_id.with_context(ctx)
                line = inv.finalize_invoice_move_lines(line)

                date = inv.date or inv.date_invoice

                move_vals = {
                    'date_maturity_current': parcel.date_maturity,
                    'date_maturity_origin': parcel.date_maturity,
                    'financial_operation_id': parcel.financial_operation_id.id,
                    'title_type_id': parcel.title_type_id.id,
                    'ref': inv.reference,
                    'line_ids': line,
                    'journal_id': journal.id,
                    'date': date,
                    'narration': inv.comment,
                    'parcel_id': parcel.id,
                    'company_id': inv.company_id.id,
                    'invoice_id': inv.id,
                }

                ctx['company_id'] = inv.company_id.id
                ctx['invoice'] = inv

                ctx_nolang = ctx.copy()
                ctx_nolang.pop('lang', None)
                move = account_move.with_context(ctx_nolang).create(move_vals)

                # Como o campo 'amout' e computavel, precisamos
                # copia-lo apos o camando create
                move.amount_origin = move.amount

                # Pass invoice in context in method post: used if you want to get
                # the same account move reference when creating the same invoice
                # after a cancelled one:
                move.post()

                # make the invoice point to that move
                # Mantido por questao de compatibilidade
                values = {
                    'move_id': move.id,
                    'date': date,
                    'move_name': move.name,
                    'number_backup': move.name,
                }

                inv.with_context(ctx).write(values)

        return True

    def _compute_residual(self):
        """Realiza calculo do valore residual a ser pago da fatura.
        """

        for inv in self:

            # Quando a fatura nao possui parcela, ela utiliza
            # o financeiro do core (antigo)
            if not inv.parcel_ids:
                super(AccountInvoice, self)._compute_residual()
            else:
                # Se entrar aqui utilizamos o novo financeiro
                # o calculo do residual é realizado sobre as account.move
                # geradas pela parcela
                residual = 0.0
                residual_company_signed = 0.0

                # Obtemos o sinal do residual, dependendo do tipo da fatura
                sign = inv.type in ['in_refund', 'out_refund'] and -1 or 1

                # A diferenca do metodo original, e que aqui iremos percorrer
                # mais de uma account.move, uma vez que no novo financeiro
                # cada parcela gera uma account.move
                for move in inv.sudo().move_ids:

                    for line in move.line_ids:

                        if line.account_id == inv.account_id:
                            residual_company_signed += line.amount_residual

                            # Caso o linha da account.move ser da mesma moeda que a fatura
                            if line.currency_id == inv.currency_id:
                                residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                            else:
                                # Caso contrario, realizamos a conversao de moeda
                                from_currency = (line.currency_id and line.currency_id.with_context(
                                    date=line.date)) or line.company_id.currency_id.with_context(date=line.date)

                                residual += from_currency.compute(
                                    line.amount_residual, inv.currency_id)

                inv.residual_company_signed = abs(residual_company_signed) * sign
                inv.residual_signed = abs(residual) * sign
                inv.residual = abs(residual)

                digits_rounding_precision = inv.currency_id.rounding

                # Verificamos se a fatura foi reconciliada quando o valor
                # residual e zero
                if float_is_zero(inv.residual, precision_rounding=digits_rounding_precision):
                    inv.reconciled = True
                else:
                    inv.reconciled = False

    @api.multi
    def action_open_periodic_entry_wizard(self):
        """Abre wizard para gerar pagamentos periodicos"""
        self.ensure_one()

        if not self.pre_invoice_date:
            raise UserError('Nenhuma data fornecida como base para a '
                            'criação das parcelas!')

        if self.state != 'draft':
            raise UserError('Parcelas podem ser criadas apenas quando a '
                            'fatura estiver como "Provisório"')

        if not self.payment_term_id:
            raise UserError('Nenhuma condição de pagamento foi fornecida. Por'
                            'favor, selecione uma condição de pagamento')

        if not self.invoice_line_ids:
            raise UserError('Nenhuma linha de fatura foi fornecida. Por '
                            'favor insira ao menos um produto/serviço')

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'br_account.invoice.parcel.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {
                'default_payment_term_id': self.payment_term_id.id,
                'default_pre_invoice_date': self.pre_invoice_date,
            },
            'views': [(False, 'form')],
            'target': 'new',
        }

        return action

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        self.action_number()
        return res

    @api.multi
    def action_br_account_invoice_open(self):
        """Metodo criado para manter a compatibilidade dos testes do core
        com o sistema de criação de parcelas do br_account. Anteriormente
        o metodo 'action_invoice_open' era chamado ao clicar no botao 'Validar'
        da Fatura. Este metodo realiza a verificacao das parcelas ao mesmo
        tempo que permite compatibilidade com os testes do core

        :return: True se o record foi salvo e False, caso contrário.
        """

        if self.parcel_ids:
            self.validate_date_maturity_from_parcels()
            if self.compare_total_parcel_value():
                return super(AccountInvoice, self).with_context(
                    use_parcel_system=True).action_invoice_open()
            else:
                raise UserError(_('O valor total da fatura e total das '
                                  'parcelas divergem! Por favor, gere as '
                                  'parcelas novamente.'))
        else:
            raise ValidationError(
                'Campo parcela está vazio. Por favor, crie as parcelas')

    @api.multi
    def action_number(self):

        for invoice in self:
            if invoice.fiscal_document_id:

                if not invoice.document_serie_id:
                    raise UserError(
                        'Configure uma série para a fatura')

                elif not invoice.document_serie_id.internal_sequence_id:
                    raise UserError(
                        'Configure a sequência para a numeração da nota')
                else:
                    seq_number = invoice.document_serie_id.internal_sequence_id.next_by_id()  # noqa: 501
                    invoice.internal_number = seq_number

        return True

    @api.multi
    def compare_total_parcel_value(self):

        # Obtemos o total dos valores da parcela
        total = sum([abs(p.parceling_value) for p in self.parcel_ids])

        # Obtemos a precisao configurada
        prec = self.env['decimal.precision'].precision_get('Account')

        # Comparamos o valor total da invoice e das parcelas
        # a fim de verificar se os valores sao os mesmos
        # float_compare retorna 0, se os valores forem iguais
        # float_compare retorna -1, se amount_total for menor que total
        # float_compare retorna 1, se amount_total for maior que total
        if float_compare(self.amount_total, total, precision_digits=prec):
            return False
        else:
            return True

    @api.multi
    def validate_date_maturity_from_parcels(self):
        """Verifica se algum registro no campo parcel_ids tem data de 
        vencimento menor que o campo pre_invoice_date da fatura.
        
        Raises:
            UserError -- Ao menos uma parcela gerada tem data de vencimento
            menor que a data de pré fatura.
        """
        for inv in self:
            if inv.journal_id.type == 'sale':
                has_incoerent_parcel = any(
                    parcel.date_maturity < inv.pre_invoice_date
                    for parcel in inv.parcel_ids)

                if has_incoerent_parcel:
                    raise UserError(_
                        ('Pelo menos um registro de parcela foi criado com '
                        'data de vencimento menor do que a data da '
                        'pré-fatura, por favor, considere verificar o campo '
                        'payment_term_id'))

    @api.multi
    def action_invoice_cancel_paid(self):
        if self.filtered(lambda inv: inv.state not in ['proforma2', 'draft',
                                                       'open', 'paid']):
            raise UserError(_("Invoice must be in draft, Pro-forma or open \
                              state in order to be cancelled."))

        return self.action_cancel()

    @api.multi
    def action_cancel(self):
        """Sobrescrita do metodo de cancelamento da Fatura. 
        Remove as account.move acopladas a fatura quando a mesma
        e confirmada. Foi necessario sobrescrever o metodo do 
        core porque a fatura agora gera uma account.move por
        parcela (após correções no financeiro).

        Raises:
            UserError -- Quando a fatura esta parcialmente paga.

        Returns:
            bool -- True quando o metodo foi executado sem erro.
        """
        moves = self.env['account.move']

        for inv in self:

            # Quando a fatura nao possui parcela, ela utiliza
            # o financeiro do core (antigo)
            if not inv.parcel_ids:
                return super(AccountInvoice, self).action_cancel()
            else:
                if inv.move_ids:
                    moves += inv.move_ids

                if any(move for move in inv.move_ids if move.paid_status == 'partial'):
                    raise UserError(
                        _('You cannot cancel an invoice which is partially paid.' \
                          'You need to unreconcile related payment entries first.'))

        # Inicialmente, alteramos o status da fatura para 'cancel' e 
        # desacoplamos as move_ids.
        # Apagamos o valor da data de confirmacao para que a geracao da
        # parcela continue consistente
        self.write({
            'state': 'cancel',
            'move_ids': False,
            'move_id': False,
            'cancel_invoice_date': fields.Date.today(),
        })

        if moves:
            # segundo, invalidamos as move(s)
            moves.button_cancel()
            # 
            # Excluimos as moves desta invoice estava apontando.
            # As move.lines e move.reconciles correspondentes serao automaticamente
            # excluidas tambem.
            moves.unlink()
        return True

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        for index, line in enumerate(self.invoice_line_ids):
            if line.quantity != 0:
                res[index]['price'] = line.price_total

        return res

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):

        res = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)

        count = 1
        for invoice_line in res:
            line = invoice_line[2]
            line['ref'] = self.origin
            if line['name'] == '/' \
                    or (line['name'] == self.name and self.name):
                line['name'] = "%02d" % count
                count += 1
        return res

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            other_taxes = line.invoice_line_tax_ids.filtered(
                lambda x: not x.domain)

            line.invoice_line_tax_ids = (other_taxes |
                                         line.tax_icms_id |
                                         line.tax_ipi_id |
                                         line.tax_pis_id |
                                         line.tax_cofins_id |
                                         line.tax_issqn_id |
                                         line.tax_ii_id |
                                         line.tax_icms_st_id |
                                         line.tax_simples_id |
                                         line.tax_csll_id |
                                         line.tax_irrf_id |
                                         line.tax_inss_id)

            ctx = line._prepare_tax_context()
            tax_ids = line.invoice_line_tax_ids.with_context(**ctx)

            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_ids.compute_all(
                price_unit, self.currency_id, line.quantity,
                line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(
                    tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()

        done_taxes = []
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount and tax_line.tax_id.deduced_account_id:
                tax = tax_line.tax_id
                done_taxes.append(tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount * -1,
                    'quantity': 1,
                    'price': tax_line.amount * -1,
                    'account_id': tax_line.tax_id.deduced_account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, done_taxes)]
                    if tax_line.tax_id.include_base_amount else []
                })
        return res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)

        res['fiscal_document_id'] = invoice.fiscal_document_id.id
        res['document_serie_id'] = invoice.document_serie_id.id
        return res

    @api.multi
    def generate_parcel_entry(self, financial_operation, title_type):
        """Cria as parcelas da fatura."""

        for inv in self:

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.pre_invoice_date:
                raise UserError('Nenhuma data fornecida como base para a '
                                'criação das parcelas!')

            if inv.state != 'draft':
                raise UserError('Parcelas podem ser criadas apenas quando a '
                                'fatura estiver como "Provisório"')

            if not inv.payment_term_id:
                raise UserError(
                    'Nenhuma condição de pagamento foi fornecida. Por'
                    'favor, selecione uma condição de pagamento')

            if not inv.invoice_line_ids:
                raise UserError('Nenhuma linha de fatura foi fornecida. Por '
                                'favor insira ao menos um produto/serviço')

            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and
            # analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency

            total, total_currency, iml = inv.with_context(
                ctx).compute_invoice_totals(company_currency, iml)

            aux = inv.with_context(ctx).payment_term_id.with_context(
                currency_id=company_currency.id).compute(
                total, inv.pre_invoice_date)

            lines_no_taxes = aux[0]

            res_amount_currency = total_currency
            ctx['date'] = inv.pre_invoice_date

            # Removemos as parcelas adicionadas anteriormente
            inv.parcel_ids.unlink()

            for i, t in enumerate(lines_no_taxes):

                if inv.currency_id != company_currency:
                    amount_currency = \
                        company_currency.with_context(ctx).compute(
                            t[1], inv.currency_id)
                else:
                    amount_currency = False

                # last line: add the diff
                res_amount_currency -= amount_currency or 0

                if i + 1 == len(lines_no_taxes):
                    amount_currency += res_amount_currency

                values = {
                    'name': str(i + 1).zfill(2),
                    'parceling_value': round(t[1], 2),
                    'date_maturity': t[0],
                    'old_date_maturity': t[0],
                    'financial_operation_id': financial_operation.id,
                    'title_type_id': title_type.id,
                    'amount_currency': diff_currency and amount_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id,
                }

                self.env['br_account.invoice.parcel'].create(values)

        return True

    @api.model
    def line_get_convert(self, line, part):
        ret = super(AccountInvoice, self).line_get_convert(line, part)

        ret['title_type_id'] = line.get('title_type_id')
        ret['financial_operation_id'] = line.get('financial_operation_id')

        return ret

    @api.model
    def _function_br_account(self):
        if self.env.ref('account.action_account_payment_from_invoices'):
            self.env.ref(
                'account.action_account_payment_from_invoices').unlink()
