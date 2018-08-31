import logging

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        """Cria fatura quando a opção de faturamento
        selecionada e porcentagem ou valor fixo. Este metodo
        copia os campos do pedido de venda para a fatura.

        Arguments:
            order {sale.order} -- Sale Order que cria a fatura.
            so_line {sale.order.line} -- Sale Order Line com os detalhes dos produtos.
            amount {float} -- Porcentagem ou valor fixo a ser aplicado no valor da fatura.

        Returns:
            [account.invoice] -- Account Invoice criada a partir da Sale Order.
        """
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(
            order=order, so_line=so_line, amount=amount)

        # Inicialmente pegamos 'title_type' e 'financial_operation'
        # apenas para criar as parcelas
        title_type = self.env.ref('br_account.account_title_type_1')
        financial_operation = self.env.ref(
            'br_account.account_financial_operation_6')

        invoice.pre_invoice_date = order.confirmation_date

        # Ao invés de copiarmos as parcelas da Sale Order, optei por
        # recriá-las. Decidi seguir essas abordagem porque o uso da porcentagem
        # ou do valor fixo fazem com que o valor total da Invoice seja truncado.
        # Sendo assim, os valores das parcelas também precisam ser recalculados.
        # Dessa forma, de modo a simplificar o algoritmo, optei por recriar as parcelas
        # já tendo como referência o valor da fatura já reajustado

        try:
            invoice.generate_parcel_entry(financial_operation=financial_operation,
                                          title_type=title_type)

            # Aqui, atualizamos cada campo da parcela da Invoice com os valores
            # da respectiva parcela na Sale Order. Apenas o valor da parcela
            # não é copiado porque o mesmo foi reajustado pra se adequar ao
            # ao valor da fatura
            for inv_parcel, order_parcel in zip(invoice.parcel_ids, order.parcel_ids):
                inv_parcel.name = order_parcel.name
                inv_parcel.date_maturity = order_parcel.date_maturity
                inv_parcel.old_date_maturity = order_parcel.old_date_maturity
                inv_parcel.financial_operation_id = order_parcel.financial_operation_id
                inv_parcel.title_type_id = order_parcel.title_type_id
                inv_parcel.pin_date = order_parcel.pin_date

        except UserError as exc:
            # Capturamos a excecao por questoes de compatibilidade com o core
             _logger.info(exc)

        fiscal_position = invoice.fiscal_position_id

        # Os campos a seguir tambem não estavam sendo copiados para a
        # Invoice criada
        invoice.fiscal_document_id = fiscal_position.fiscal_document_id
        invoice.document_serie_id = fiscal_position.document_serie_id

        invoice.fiscal_observation_ids = [
            (6, None, fiscal_position.fiscal_observation_ids.ids),
        ]

        return invoice
