# © 2009 Renato Lima - Akretion
# © 2012 Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# © 2018 Michell Stuttgart, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    STATES = {
        'draft': [('readonly', False)],
    }

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()

        if self.fiscal_position_id:
            if self.fiscal_position_id.account_id:
                res['account_id'] = self.fiscal_position_id.account_id.id

            if self.fiscal_position_id.journal_id:
                res['journal_id'] = self.fiscal_position_id.journal_id.id

            if self.fiscal_position_id.fiscal_document_id:
                res['fiscal_document_id'] = self.fiscal_position_id.fiscal_document_id.id

            if self.fiscal_position_id.document_serie_id:
                res['document_serie_id'] = self.fiscal_position_id.document_serie_id.id

            if self.parcel_ids:
                parcel_values = [(0, 0, self._get_parcel_to_invoice(rec))
                                 for rec in self.parcel_ids]

                res['parcel_ids'] = parcel_values

            if self.fiscal_position_id.fiscal_observation_ids:
                res['fiscal_observation_ids'] = [
                    (6, None, self.fiscal_position_id.fiscal_observation_ids.ids),
                ]
        return res

    def _get_parcel_to_invoice(self, parcel):
        """ Metodo para gerar dicionario das parcelas.
        Arguments:
            parcel {BrSaleParcel} -- record com objeto BrSaleParcel.

        Returns:
            dict -- valores para gerar parcelas da 'br_sale.parcel' na 'br_account.invoice.parcel'
        """
        return {
            'date_maturity': parcel.date_maturity,
            'name': parcel.name,
            'parceling_value': parcel.parceling_value,
            'financial_operation_id': parcel.financial_operation_id.id,
            'title_type_id': parcel.title_type_id.id,
            'pin_date': parcel.pin_date,
            'amount_days': parcel.amount_days,
        }

    total_bruto = fields.Float(string='Total Bruto ( = )',
                               readonly=True,
                               compute='_amount_all',
                               digits=dp.get_precision('Account'), store=True)

    total_tax = fields.Float(string='Impostos ( + )',
                             readonly=True,
                             compute='_amount_all',
                             digits=dp.get_precision('Account'),
                             store=True)

    total_desconto = fields.Float(string='Desconto Total ( - )',
                                  readonly=True,
                                  compute='_amount_all',
                                  digits=dp.get_precision('Account'),
                                  store=True,
                                  help="The discount amount.")

    parcel_ids = fields.One2many(comodel_name='br_sale.parcel',
                                 inverse_name='sale_order_id',
                                 readonly=True,
                                 states=STATES,
                                 string='Parcelas')

    quotation_date = fields.Date(string='Data da Cotação',
                                 required=True,
                                 copy=False,
                                 default=fields.Date.today)

    @api.depends('order_line.price_total', 'order_line.valor_desconto')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            price_total = sum(l.price_total for l in order.order_line)
            price_subtotal = sum(l.price_subtotal for l in order.order_line)
            order.update({
                'total_tax': price_total - price_subtotal,
                'total_desconto': sum(l.valor_desconto for l in order.order_line),
                'total_bruto': sum(l.valor_bruto for l in order.order_line),
            })

    @api.multi
    def action_open_periodic_entry_wizard(self):
        """Abre wizard para gerar pagamentos periodicos

        Raises:
            UserError -- Caso não tenha data de cotação.
            UserError -- Caso a cotação esteja em um state diferente de 'draft'.
            UserError -- Caso a cotação não tenha condição de pagamento.

        Returns:
            wizard: instancia de 'br_sale.parcel.wizard' gerar as parcelas da cotação.
        """

        self.ensure_one()

        msg = ''

        if not self.quotation_date:
            msg = 'Nenhuma data fornecida como base para a '
            'criação das parcelas!'

        if self.state != 'draft':
            msg = 'Parcelas podem ser criadas apenas quando a '
            'cotação estiver como "Provisório"'

        if not self.payment_term_id:
            msg = 'Nenhuma condição de pagamento foi fornecida. Por'
            'favor, selecione uma condição de pagamento'

        if msg:
            raise UserError(msg)

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'br_sale.parcel.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {
                'default_payment_term_id': self.payment_term_id.id,
                'default_pre_sale_order_date': self.quotation_date,
            },
            'views': [(False, 'form')],
            'target': 'new',
        }

        return action

    @api.multi
    def generate_parcel_entry(self, financial_operation, title_type):
        """Cria as parcelas da cotação

        Raises:
            UserError -- Caso não tenha data de cotação.
            UserError -- Caso a cotação esteja em um state diferente de 'draft'.
            UserError -- Caso a cotação não tenha condição de pagamento.

        Returns:
            bool -- True
        """

        for inv in self:

            ctx = dict(self._context, lang=inv.partner_id.lang)

            msg = ''

            if not inv.quotation_date:
                msg = 'Nenhuma data fornecida como base para a criação' 
                'das parcelas!'

            if inv.state != 'draft':
                msg = 'Parcelas podem ser criadas apenas quando a'
                'cotação estiver como "Provisório"'

            if not inv.payment_term_id:
                msg = 'Nenhuma condição de pagamento foi fornecida. Por'
                'favor, selecione uma condição de pagamento'

            if msg:
                raise UserError(msg)

            company_currency = inv.company_id.currency_id

            diff_currency = inv.currency_id != company_currency

            total = self.amount_total

            aux = inv.with_context(ctx).payment_term_id.with_context(
                currency_id=company_currency.id).compute(
                total, inv.quotation_date)

            lines_no_taxes = aux[0]

            res_amount_currency = total
            ctx['date'] = inv.quotation_date

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
                    'parceling_value': t[1],
                    'date_maturity': t[0],
                    'old_date_maturity': t[0],
                    'financial_operation_id': financial_operation.id,
                    'title_type_id': title_type.id,
                    'amount_currency': diff_currency and amount_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'sale_order_id': inv.id,
                }

                self.env['br_sale.parcel'].create(values)

        return True
